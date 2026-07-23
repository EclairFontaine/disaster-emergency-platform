import { useState, useEffect } from 'react'
import { Card, Form, Input, Select, InputNumber, Button, message, Table, Tag, Space, Upload } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import MapView from '../../components/MapView'
import { api } from '../../services/api'
import { useAppStore } from '../../store'

const { TextArea } = Input

const severityColors: Record<string, string> = { P1: 'red', P2: 'orange', P3: 'blue', P4: 'green' }
const statusLabels: Record<string, string> = { pending_review: '待核验', confirmed: '已确认', in_progress: '处置中', closed: '已结束' }

export default function IncidentReport() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [reports, setReports] = useState<any[]>([])
  const [images, setImages] = useState<string[]>([])

  const loadReports = () => {
    api.listIncidents({ limit: 50 }).then((data) => setReports(data))
  }
  useEffect(() => { loadReports() }, [])

  const handleMapClick = (pos: { lng: number; lat: number }) => {
    form.setFieldsValue({ latitude: pos.lat.toFixed(6), longitude: pos.lng.toFixed(6) })
  }

  const handleUpload = async (file: File) => {
    try {
      const reader = new FileReader()
      reader.onload = () => {
        setImages((prev) => [...prev, reader.result as string])
      }
      reader.readAsDataURL(file)
      message.success('上传成功')
    } catch {
      message.error('上传失败')
    }
    return false
  }

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const incident = await api.createIncident(values)
      if (images.length > 0) {
        await api.createReport(incident.id, {
          content: values.description || '灾情报告附件',
          images,
          latitude: values.latitude,
          longitude: values.longitude,
        })
      }
      message.success('灾情上报成功')
      form.resetFields()
      setImages([])
      loadReports()
    } catch (err: any) {
      message.error(err.response?.data?.detail || '上报失败')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '类型', dataIndex: 'category', key: 'category', render: (v: string) => v || '-' },
    { title: '严重度', dataIndex: 'severity', key: 'severity', render: (s: string) => <Tag color={severityColors[s]}>{s}</Tag> },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => statusLabels[s] || s },
    { title: '时间', dataIndex: 'created_at', key: 'created_at', render: (t: string) => t ? new Date(t).toLocaleString('zh-CN') : '-' },
  ]

  return (
    <div>
      <Card title="灾情上报" style={{ marginBottom: 16 }}>
        <Form form={form} onFinish={onFinish} layout="vertical" initialValues={{ severity: 'P3', category: 'other' }}>
          <Form.Item name="title" label="灾情标题" rules={[{ required: true, message: '请输入标题' }]}>
            <Input placeholder="简要描述灾情" />
          </Form.Item>
          <Form.Item name="description" label="详细描述" rules={[{ required: true, message: '请输入描述' }]}>
            <TextArea rows={4} placeholder="请详细描述灾情情况" />
          </Form.Item>
          <Space size="large" style={{ marginBottom: 16 }}>
            <Form.Item name="category" label="灾害类型" style={{ marginBottom: 0 }}>
              <Select style={{ width: 160 }} options={[
                { value: 'earthquake', label: '地震' }, { value: 'flood', label: '洪水' },
                { value: 'landslide', label: '山体滑坡' }, { value: 'fire', label: '火灾' },
                { value: 'other', label: '其他' },
              ]} />
            </Form.Item>
            <Form.Item name="severity" label="严重程度" style={{ marginBottom: 0 }}>
              <Select style={{ width: 160 }} options={[
                { value: 'P1', label: 'P1-特别重大' }, { value: 'P2', label: 'P2-重大' },
                { value: 'P3', label: 'P3-较大' }, { value: 'P4', label: 'P4-一般' },
              ]} />
            </Form.Item>
            <Form.Item name="affected_count" label="影响人数" style={{ marginBottom: 0 }}>
              <InputNumber min={0} />
            </Form.Item>
          </Space>

          <Card title="选择位置" size="small" style={{ marginBottom: 16 }}>
            <MapView height={300} onMapClick={handleMapClick} />
            <Space style={{ marginTop: 8 }}>
              <Form.Item name="latitude" label="纬度" style={{ marginBottom: 0 }}>
                <Input readOnly style={{ width: 140 }} />
              </Form.Item>
              <Form.Item name="longitude" label="经度" style={{ marginBottom: 0 }}>
                <Input readOnly style={{ width: 140 }} />
              </Form.Item>
            </Space>
          </Card>

          <Form.Item label="图片上传">
            <Upload beforeUpload={(file) => { handleUpload(file); return false }} showUploadList={false} accept="image/*">
              <Button icon={<UploadOutlined />}>选择图片</Button>
            </Upload>
            {images.length > 0 && (
              <Space style={{ marginTop: 8 }}>
                {images.map((url, i) => (
                  <img key={i} src={url} alt="" style={{ width: 100, height: 100, objectFit: 'cover', borderRadius: 4 }} />
                ))}
              </Space>
            )}
          </Form.Item>

          <Button type="primary" htmlType="submit" loading={loading}>提交上报</Button>
        </Form>
      </Card>

      <Card title="我的上报记录">
        <Table dataSource={reports} columns={columns} rowKey="id" size="small" />
      </Card>
    </div>
  )
}
