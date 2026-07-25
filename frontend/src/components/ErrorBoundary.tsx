import { Component, ReactNode } from 'react'
import { Button, Result } from 'antd'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="页面出现异常"
          subTitle={this.state.error?.message || '未知错误'}
          extra={[
            <Button type="primary" key="retry" onClick={this.handleRetry}>重试</Button>,
            <Button key="reload" onClick={() => window.location.reload()}>刷新页面</Button>,
          ]}
        />
      )
    }
    return this.props.children
  }
}
