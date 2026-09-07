-- 保险初始化数据（车辆id=2，沃尔沃XC60 京JU1515）
-- 幂等：按保单号判断，已存在则跳过

-- 交强险
INSERT INTO insurance_policies (vehicle_id, company, policy_no, policy_type, items_json, premium, vehicle_tax, service_phone, vehicle_model, plate_no, start_date, end_date, note, created_at)
SELECT 2, '中国人民财产保险股份有限公司北京市门头沟支公司', 'PDZA202511010001562924', '交强险',
  '["死亡伤残赔偿限额180000元","医疗费用赔偿限额18000元","财产损失赔偿限额2000元"]',
  541.87, 400.00, '95518', '沃尔沃VCC6474E52U多用途乘用车', '京JU1515', '2025-12-17', '2026-12-16',
  '被保险人李孟强；完税凭证号B25D30526782；尾号限行减免53天减免保费75.63元',
  NOW()
WHERE NOT EXISTS (SELECT 1 FROM insurance_policies WHERE policy_no = 'PDZA202511010001562924');

-- 商业险
INSERT INTO insurance_policies (vehicle_id, company, policy_no, policy_type, items_json, premium, vehicle_tax, service_phone, vehicle_model, plate_no, start_date, end_date, note, created_at)
SELECT 2, '中国人民财产保险股份有限公司北京市门头沟支公司', 'PDAA202511010001192446', '商业险',
  '["机动车损失保险(保额200841.40元,保费1508.43元)","机动车第三者责任保险(保额3500000元,保费519.99元)","车上人员责任险司机(10000元/座*1座,保费8.79元)","车上人员责任险乘客(10000元/座*4座,保费22.31元)","附加医保外医疗费用责任险(保额200000元,保费11.37元)","附加道路救援服务(7次,0元)","附加车辆安全检测(1次,0元)","附加代为驾驶服务(1次,0元)","附加代为送检服务(1次,0元)"]',
  2070.89, 0, '95518', '沃尔沃VCC6474E52U多用途乘用车', '京JU1515', '2025-12-17', '2026-12-16',
  '被保险人李孟强；销售渠道保险公司门店直销；经办人李海萁',
  NOW()
WHERE NOT EXISTS (SELECT 1 FROM insurance_policies WHERE policy_no = 'PDAA202511010001192446');
