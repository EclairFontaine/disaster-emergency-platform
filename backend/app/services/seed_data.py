"""云南应急平台种子数据 - 提供完整的演示数据"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.all import (
    User, EmergencyPlan, Incident, Resource, DataSource, DispatchOrder, IncidentReport
)
from app.core.security import hash_password


EMERGENCY_PLANS = [
    {
        "title": "云南省地震应急预案",
        "content": """一、总则
云南省地处印度板块与欧亚板块碰撞带东侧，地震活动频繁。本预案适用于云南省行政区域内发生的破坏性地震灾害事件。

二、应急响应分级
1. 特别重大地震灾害（I级响应）：造成300人以上死亡，或直接经济损失占全省上年生产总值1%以上。
2. 重大地震灾害（II级响应）：造成50人以上、300人以下死亡。
3. 较大地震灾害（III级响应）：造成10人以上、50人以下死亡。
4. 一般地震灾害（IV级响应）：造成10人以下死亡。

三、组织机构
成立省抗震救灾指挥部，由省长任指挥长，下设综合协调组、抢险救援组、医疗救治组、群众安置组、交通保障组、物资保障组、通信保障组、次生灾害防控组、信息发布组。

四、处置措施
1. 立即启动应急响应，集结专业救援力量。
2. 组织受灾群众疏散转移至安全区域。
3. 设立临时避难场所，保障基本生活需求。
4. 开展生命搜救，72小时黄金救援期内全力施救。
5. 组织医疗队伍开展伤员救治和卫生防疫。
6. 抢修受损基础设施（道路、电力、通信、供水）。
7. 开展次生灾害监测防控（滑坡、泥石流、堰塞湖等）。
8. 及时发布灾情信息和救援进展。

五、资源保障
- 省级储备库：帐篷10万顶、棉被50万床、折叠床20万张
- 救援队伍：消防总队2000人、武警总队3000人
- 医疗资源：省级医疗队30支、野战医院5所
- 通信设备：卫星电话500部、应急通信车20辆"""
    },
    {
        "title": "云南省防汛抗旱应急预案",
        "content": """一、总则
云南地形复杂，山区面积占94%，汛期暴雨集中，极易引发山洪、滑坡、泥石流等灾害。

二、预警分级
- 红色预警（I级）：3小时内降雨量将达100毫米以上
- 橙色预警（II级）：3小时内降雨量将达50毫米以上
- 黄色预警（III级）：6小时内降雨量将达50毫米以上
- 蓝色预警（IV级）：12小时内降雨量将达50毫米以上

三、应急响应
1. 监测预警：水文站、气象站实时监测，每1小时报告一次。
2. 群众转移：低洼地区、山洪危险区群众提前转移到安全地带。
3. 水库调度：科学调度水库泄洪，确保大坝安全。
4. 堤防抢险：组织力量加固堤防，封堵决口。
5. 城市排涝：启动排涝泵站，疏浚排水管道。
6. 灾后防疫：开展环境消杀，确保饮用水安全。

四、重点防御区域
怒江流域、澜沧江流域、红河流域、金沙江流域的河谷地带及山洪易发区。"""
    },
    {
        "title": "云南省森林火灾应急预案",
        "content": """一、总则
云南省森林覆盖率超过65%，冬春季节干旱少雨，森林火险等级高。

二、火险等级
依据气象条件、可燃物干燥度、火源等因素评定五级火险。

三、应急响应
1. 火情监测：卫星遥感+无人机巡航+地面瞭望塔三重监控。
2. 火情报告：发现火情立即报告，10分钟内出动。
3. 扑救力量：森林消防总队2000人+地方专业扑火队5000人。
4. 航空灭火：调用直升机洒水灭火，开设隔离带。
5. 后勤保障：保障扑火队伍给养、油料、车辆。
6. 火场管理：设立前线指挥部，统一指挥调度。
7. 善后处置：火场清理看守72小时以上，防止复燃。

四、重点防火区域
迪庆、丽江、大理、楚雄、昆明、玉溪等滇中及滇西北林区。"""
    },
    {
        "title": "云南省地质灾害应急预案",
        "content": """一、总则
云南地质构造复杂，地质灾害发育，主要有滑坡、泥石流、崩塌、地面塌陷等类型。

二、重点防治区域
- 怒江州：福贡、贡山为全国泥石流高发区
- 昭通市：镇雄、彝良等地滑坡风险高
- 红河州：元阳、金平梯田区滑坡易发
- 迪庆州：德钦、维西高山峡谷地质灾害多发

三、应急响应措施
1. 监测预警：地质灾害隐患点安装自动化监测设备。
2. 群众避险：发出预警后立即组织受威胁群众转移。
3. 工程治理：对重大隐患点实施工程治理。
4. 应急调查：派遣专家组赴现场评估风险。
5. 交通管制：对危险路段实施交通管制。
6. 临时安置：设置临时安置点，保障群众生活。"""
    },
    {
        "title": "云南省突发公共卫生事件应急预案",
        "content": """一、总则
建立统一领导、分级负责、反应及时、措施果断、依靠科学、加强合作的应急处置机制。

二、响应分级
特别重大（I级）、重大（II级）、较大（III级）、一般（IV级）。

三、处置措施
1. 病例监测与报告：医疗机构发现聚集性病例立即报告。
2. 流行病学调查：追踪感染源和密切接触者。
3. 医疗救治：指定定点医院，集中收治患者。
4. 隔离管控：对疫区实施封锁隔离。
5. 卫生消杀：对疫点进行终末消毒。
6. 健康宣教：发布防护指南，消除恐慌。
7. 物资保障：储备防护用品、检测试剂、救治药品。"""
    },
    {
        "title": "云南省低温雨雪冰冻灾害应急预案",
        "content": """一、总则
云南滇东北、滇西北高海拔地区冬季易发生低温雨雪冰冻灾害。

二、重点区域
昭通大山包、迪庆香格里拉、丽江玉龙雪山、大理苍山等高海拔地区。

三、处置措施
1. 交通保障：对结冰路段撒盐除冰，必要时封路。
2. 电力保障：抢修覆冰线路，确保供电。
3. 民生保障：向困难群众发放御寒物资。
4. 农业防冻：指导农户做好农作物和牲畜防冻。
5. 应急救助：设立临时救助站，救助滞留人员。"""
    },
    {
        "title": "大理州地震灾害应急处置方案",
        "content": """针对大理白族自治州的地震应急处置方案。
大理州地处滇西地震带，历史上曾发生1925年大理7.0级地震。
重点防范区域：大理市、漾濞县、洱源县、祥云县。

救援力量部署：
- 大理州消防救援支队：500人
- 大理州武警支队：800人
- 省级地震救援队：200人（24小时备勤）

避难场所：大理全民健身中心、大理古城南门广场、下关文化广场等30处。
医疗资源：大理州人民医院、大理大学附属医院为定点救治医院。

应急物资储备点：
- 大理市应急物资库：帐篷5000顶、棉被10000床
- 漾濞县物资库：帐篷2000顶、棉被5000床"""
    },
    {
        "title": "怒江州泥石流灾害应急处置方案",
        "content": """怒江傈僳族自治州是全国泥石流灾害最严重的地区之一。

重点监测点：福贡县上帕镇、匹河乡，贡山县丙中洛镇、茨开镇。

预警机制：
- 安装雨量站50处、泥水位监测站30处
- 群测群防人员200人每日巡查
- 危险区设置预警广播和撤离路线标识

应急响应：
1. 蓝色预警：通知村组干部做好巡查
2. 黄色预警：危险区人员做好撤离准备
3. 橙色预警：组织危险区群众撤离
4. 红色预警：强制撤离并封锁危险区域

近期重点：
怒江美丽公路沿线边坡加固工程，贡山县城泥石流沟治理项目。"""
    },
    {
        "title": "昆明市突发公共事件总体应急预案",
        "content": """一、总则
昆明市作为云南省省会，人口密集，经济集中。本预案适用于各类突发公共事件。

二、响应机制
1. 监测预警：依托市应急指挥中心，建立多部门信息共享机制。
2. 分级响应：一般事件由区级处置，较大以上由市级统一指挥。
3. 应急联动：公安、消防、医疗、交通、电力等部门协同。

三、应急资源
- 主城区58处应急避难场所，可容纳200万人
- 消防支队2000人、武警1000人、民兵5000人
- 三甲医院15家，社区卫生服务中心120个"""
    },
    {
        "title": "云南省重大动物疫情应急预案",
        "content": """一、总则
云南是畜牧业大省，生猪存栏3000万头以上。本预案适用于突发重大动物疫情应急处置。

二、处置措施
1. 疫情报告：养殖户/兽医发现疑似疫情立即上报，2小时内到省级。
2. 封锁隔离：划定疫点、疫区、受威胁区，实施封锁。
3. 扑杀无害化处理：疫点内易感动物全部扑杀。
4. 消毒灭源：对疫区全面消毒。
5. 紧急免疫：受威胁区易感动物紧急免疫接种。"""
    },
    {
        "title": "云南省通信保障应急预案",
        "content": """一、总则
确保自然灾害中通信畅通，为应急指挥提供通信保障。

二、应急通信手段
1. 公网恢复：优先恢复电信、移动、联通公网。
2. 卫星电话：500部卫星电话、50套便携卫星站。
3. 应急通信车：20辆，30分钟内建立临时覆盖。
4. 短波电台：各县配置短波电台作为最后保障。
5. 无人机中继：10架通信中继无人机覆盖山区盲区。"""
    },
    {
        "title": "云南省电力保障应急预案",
        "content": """一、总则
保障电网安全运行，快速恢复受损电力设施。

二、应急措施
1. 电力调度：事故后立即调整电网运行方式，隔离故障。
2. 线路抢修：调集专业队伍，优先恢复重要用户供电。
3. 移动电源：应急发电车保障医院、指挥中心等重点场所。
4. 抢修资源：云南电网100支队伍、80辆发电车、3个中心物资仓库。"""
    },
    {
        "title": "云南省突发环境事件应急预案",
        "content": """一、总则
有效处置突发环境事件，保护生态环境和公众健康。

二、主要风险
1. 矿山尾矿库：全省300余座，部分位于河流上游。
2. 化工企业：集中在安宁、曲靖、开远等地。
3. 危化品运输：昆曼公路、滇缅公路等国际通道。
4. 跨境河流：澜沧江、怒江、红河水污染风险。

三、应急措施
切断污染源、加密水质监测、必要时关闭取水口启用备用水源、通知下游停止使用受污染水体、开展生态修复。涉及跨境河流时立即外交部通报下游国家。"""
    },
]

SAMPLE_INCIDENTS = [
    {"title":"大理漾濞县5.2级地震","description":"漾濞县发生5.2级地震，震源深8km，震中位于苍山西坡，震感强烈，老房裂缝","category":"earthquake","severity":"P2","latitude":25.68,"longitude":99.95,"affected_count":8500,"risk_radius":5000},
    {"title":"怒江福贡县特大山洪泥石流","description":"福贡县上帕镇特大泥石流，冲毁民房15间，2人失联，美丽公路中断","category":"landslide","severity":"P1","latitude":26.90,"longitude":98.87,"affected_count":3200,"risk_radius":3000},
    {"title":"昭通镇雄县山体滑坡","description":"镇雄赤水源镇滑坡约5万方，掩埋1户民房，3人被困","category":"landslide","severity":"P2","latitude":27.37,"longitude":105.0,"affected_count":500,"risk_radius":2000},
    {"title":"丽江玉龙县拉市海森林火灾","description":"玉龙拉市海附近林火，过火约200亩，火势向东北蔓延","category":"fire","severity":"P2","latitude":26.93,"longitude":100.15,"affected_count":1200,"risk_radius":8000},
    {"title":"红河元阳县梯田区滑坡险情","description":"元阳新街镇滑坡裂缝扩大，威胁下方3个村寨500余户","category":"landslide","severity":"P3","latitude":23.18,"longitude":102.83,"affected_count":2100,"risk_radius":4000},
    {"title":"昆明寻甸县4.8级地震","description":"寻甸县仁德街道发生4.8级地震，部分老旧房屋受损","category":"earthquake","severity":"P3","latitude":25.56,"longitude":103.26,"affected_count":3000,"risk_radius":4000},
    {"title":"楚雄大姚县洪涝灾害","description":"大姚县持续暴雨引发洪涝，农田被淹1200亩，转移群众800人","category":"flood","severity":"P2","latitude":26.12,"longitude":101.32,"affected_count":3200,"risk_radius":6000},
    {"title":"普洱景东县6.2级地震","description":"景东县文井镇6.2级强震，震源12km，房屋倒塌82间","category":"earthquake","severity":"P1","latitude":24.32,"longitude":100.83,"affected_count":15000,"risk_radius":8000},
    {"title":"德宏芒市暴雨内涝","description":"芒市城区单日降雨量158mm，城区大面积内涝，交通瘫痪","category":"flood","severity":"P2","latitude":24.43,"longitude":98.59,"affected_count":8000,"risk_radius":5000},
    {"title":"迪庆德钦县雪灾","description":"德钦白马雪山暴雪，积雪深度超1m，214国道中断，游客被困","category":"other","severity":"P2","latitude":28.49,"longitude":98.91,"affected_count":600,"risk_radius":8000},
    {"title":"曲靖会泽县冰雹灾害","description":"会泽县突降冰雹，最大直径3cm，农作物受灾5000亩","category":"other","severity":"P3","latitude":26.42,"longitude":103.29,"affected_count":4000,"risk_radius":4000},
    {"title":"西双版纳勐海县森林大火","description":"勐海县打洛镇边境林火，过火超500亩，威胁自然保护区","category":"fire","severity":"P1","latitude":21.97,"longitude":100.47,"affected_count":800,"risk_radius":10000},
    {"title":"保山腾冲县泥石流","description":"腾冲火山群景区泥石流，阻断景区道路，滞留游客200人","category":"landslide","severity":"P3","latitude":25.02,"longitude":98.49,"affected_count":700,"risk_radius":3000},
    {"title":"文山丘北县暴雨洪涝","description":"丘北县12小时内降雨量120mm，12个村寨被淹","category":"flood","severity":"P2","latitude":24.03,"longitude":104.19,"affected_count":5500,"risk_radius":5000},
    {"title":"临沧云县地震","description":"云县爱华镇4.3级地震，震感明显，暂无房屋倒塌","category":"earthquake","severity":"P4","latitude":24.44,"longitude":100.13,"affected_count":2000,"risk_radius":3000},
    {"title":"玉溪通海县森林火灾","description":"通海县秀山公园附近林火，火线长约3公里，调集500人扑救","category":"fire","severity":"P2","latitude":24.09,"longitude":102.76,"affected_count":1500,"risk_radius":6000},
]


RESOURCES = [
    {"type": "personnel", "name": "云南省消防救援总队", "quantity": 2000, "available_qty": 1850, "latitude": 25.04, "longitude": 102.68, "contact_info": "张队长 138****6789"},
    {"type": "personnel", "name": "云南省武警总队救援支队", "quantity": 3000, "available_qty": 2800, "latitude": 25.04, "longitude": 102.70, "contact_info": "王支队长 139****8901"},
    {"type": "personnel", "name": "大理州消防救援队", "quantity": 500, "available_qty": 480, "latitude": 25.59, "longitude": 100.23, "contact_info": "李队长 135****2345"},
    {"type": "personnel", "name": "昆明蓝天救援队", "quantity": 150, "available_qty": 140, "latitude": 25.04, "longitude": 102.65, "contact_info": "陈队长 186****4567"},
    {"type": "vehicle", "name": "应急救援指挥车", "quantity": 30, "available_qty": 25, "latitude": 25.04, "longitude": 102.68},
    {"type": "vehicle", "name": "消防水罐车", "quantity": 80, "available_qty": 72, "latitude": 25.04, "longitude": 102.68},
    {"type": "vehicle", "name": "医疗救护车", "quantity": 60, "available_qty": 55, "latitude": 25.04, "longitude": 102.69},
    {"type": "vehicle", "name": "工程抢险车", "quantity": 40, "available_qty": 38, "latitude": 25.04, "longitude": 102.70},
    {"type": "material", "name": "救灾帐篷", "quantity": 10000, "available_qty": 9200, "latitude": 25.02, "longitude": 102.72},
    {"type": "material", "name": "棉被", "quantity": 50000, "available_qty": 48000, "latitude": 25.02, "longitude": 102.72},
    {"type": "material", "name": "折叠床", "quantity": 20000, "available_qty": 19000, "latitude": 25.02, "longitude": 102.72},
    {"type": "material", "name": "饮用水(箱)", "quantity": 50000, "available_qty": 48000, "latitude": 25.03, "longitude": 102.70},
    {"type": "material", "name": "方便食品(箱)", "quantity": 30000, "available_qty": 29000, "latitude": 25.03, "longitude": 102.70},
    {"type": "shelter", "name": "昆明市体育馆避难所", "quantity": 1, "available_qty": 1, "latitude": 25.04, "longitude": 102.71, "contact_info": "容纳5000人"},
    {"type": "shelter", "name": "大理全民健身中心", "quantity": 1, "available_qty": 1, "latitude": 25.59, "longitude": 100.23, "contact_info": "容纳3000人"},
    {"type": "shelter", "name": "丽江市体育馆避难所", "quantity": 1, "available_qty": 1, "latitude": 26.87, "longitude": 100.23, "contact_info": "容纳2000人"},
    {"type": "shelter", "name": "昭通市体育场避难所", "quantity": 1, "available_qty": 1, "latitude": 27.34, "longitude": 103.72, "contact_info": "容纳3000人"},
    {"type": "shelter", "name": "普洱市文化广场避难所", "quantity": 1, "available_qty": 1, "latitude": 22.78, "longitude": 100.97, "contact_info": "容纳2000人"},
]

DATA_SOURCES = [
    {"name": "中国地震台网(CENC)", "type": "warning", "url": "http://www.ceic.ac.cn", "fetch_interval": 1800, "is_active": True},
    {"name": "USGS全球地震监测", "type": "warning", "url": "https://earthquake.usgs.gov/fdsnws/event/1/", "fetch_interval": 3600, "is_active": True},
    {"name": "中央气象台(NMC)", "type": "weather", "url": "http://www.nmc.cn", "fetch_interval": 1800, "is_active": True},
    {"name": "OpenWeatherMap", "type": "weather", "url": "https://api.openweathermap.org", "fetch_interval": 3600, "is_active": False},
    {"name": "国家突发事件预警信息网", "type": "warning", "url": "http://www.12379.cn", "fetch_interval": 3600, "is_active": True},
    {"name": "云南省应急管理厅", "type": "news", "url": "http://yjglt.yn.gov.cn", "fetch_interval": 7200, "is_active": True},
    {"name": "云南省水利厅(水文)", "type": "weather", "url": "http://wcb.yn.gov.cn", "fetch_interval": 3600, "is_active": True},
]


async def seed_demo_data(db: AsyncSession):
    from sqlalchemy import delete as sqla_delete
    from app.models.all import IncidentReport, AgentRun, Citation, AuditLog, ResourceLock, DispatchOrder

    # Delete in correct order (children first to avoid FK violations)
    await db.execute(sqla_delete(Citation))
    await db.execute(sqla_delete(AgentRun))
    await db.execute(sqla_delete(IncidentReport))
    await db.execute(sqla_delete(ResourceLock))
    await db.execute(sqla_delete(DispatchOrder))
    await db.execute(sqla_delete(AuditLog))
    await db.execute(sqla_delete(Incident))
    await db.execute(sqla_delete(Resource))
    await db.execute(sqla_delete(EmergencyPlan))
    await db.execute(sqla_delete(DataSource))
    await db.flush()

    # Re-insert everything
    for p in EMERGENCY_PLANS:
        db.add(EmergencyPlan(title=p["title"], content=p["content"], generated_by="manual"))
    await db.flush()

    for r in RESOURCES:
        db.add(Resource(**r))
    await db.flush()

    for ds in DATA_SOURCES:
        db.add(DataSource(**ds))
    await db.flush()

    now = datetime.now(timezone.utc)
    for i, inc in enumerate(SAMPLE_INCIDENTS):
        status = "closed" if i >= 10 else ("in_progress" if i >= 6 else ("confirmed" if i >= 3 else "pending_review"))
        incident = Incident(
            title=inc["title"], description=inc["description"],
            category=inc["category"], severity=inc["severity"],
            latitude=inc["latitude"], longitude=inc["longitude"],
            affected_count=inc["affected_count"], risk_radius=inc["risk_radius"],
            reported_by=1, status=status,
            confirmed_by=1 if status != "pending_review" else None,
            confirmed_at=now - timedelta(hours=i+1) if status != "pending_review" else None,
            resolved_at=now - timedelta(hours=1) if status == "closed" else None,
            created_at=now - timedelta(hours=i+3),
        )
        db.add(incident)
    await db.flush()

    await db.commit()
    return {"plans":len(EMERGENCY_PLANS),"resources":len(RESOURCES),"datasources":len(DATA_SOURCES),"incidents":len(SAMPLE_INCIDENTS)}
