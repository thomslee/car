-- 加油记录初始数据导入（10条，从用户截图提取）
-- 幂等：已存在相同 vehicle_id + refueled_at + station 的记录跳过
-- 车辆ID=2（线上沃尔沃XC60），里程留空(NULL)

INSERT INTO refuel_records (vehicle_id, refueled_at, mileage, fuel_amount_l, unit_price, total_cost, paid_amount, fuel_grade, station, fuel_type, is_full, note, created_at)
SELECT 2, '2026-08-08 13:07:00', NULL, 35.38, 8.48, 300.00, 275.00, '95', '中国石化安宁庄加油站', '汽油', 1, '', NOW()
WHERE NOT EXISTS (SELECT 1 FROM refuel_records WHERE vehicle_id=2 AND refueled_at='2026-08-08 13:07:00' AND station='中国石化安宁庄加油站');

INSERT INTO refuel_records (vehicle_id, refueled_at, mileage, fuel_amount_l, unit_price, total_cost, paid_amount, fuel_grade, station, fuel_type, is_full, note, created_at)
SELECT 2, '2026-06-12 12:44:00', NULL, 27.74, 8.96, 248.50, 248.50, '95', '中国石化西门加油站', '汽油', 1, '', NOW()
WHERE NOT EXISTS (SELECT 1 FROM refuel_records WHERE vehicle_id=2 AND refueled_at='2026-06-12 12:44:00' AND station='中国石化西门加油站');

INSERT INTO refuel_records (vehicle_id, refueled_at, mileage, fuel_amount_l, unit_price, total_cost, paid_amount, fuel_grade, station, fuel_type, is_full, note, created_at)
SELECT 2, '2026-06-09 10:49:00', NULL, 30.99, 8.89, 275.50, 263.50, '95', '中国石化安宁庄加油站', '汽油', 1, '', NOW()
WHERE NOT EXISTS (SELECT 1 FROM refuel_records WHERE vehicle_id=2 AND refueled_at='2026-06-09 10:49:00' AND station='中国石化安宁庄加油站');

INSERT INTO refuel_records (vehicle_id, refueled_at, mileage, fuel_amount_l, unit_price, total_cost, paid_amount, fuel_grade, station, fuel_type, is_full, note, created_at)
SELECT 2, '2026-05-26 09:47:00', NULL, 22.38, 9.34, 209.00, 197.00, '95', '中国石化回龙观加油站', '汽油', 1, '', NOW()
WHERE NOT EXISTS (SELECT 1 FROM refuel_records WHERE vehicle_id=2 AND refueled_at='2026-05-26 09:47:00' AND station='中国石化回龙观加油站');

INSERT INTO refuel_records (vehicle_id, refueled_at, mileage, fuel_amount_l, unit_price, total_cost, paid_amount, fuel_grade, station, fuel_type, is_full, note, created_at)
SELECT 2, '2026-03-22 15:16:00', NULL, 25.71, 8.13, 209.00, 200.00, '95', '中国石化羊坊北加油站', '汽油', 1, '', NOW()
WHERE NOT EXISTS (SELECT 1 FROM refuel_records WHERE vehicle_id=2 AND refueled_at='2026-03-22 15:16:00' AND station='中国石化羊坊北加油站');

INSERT INTO refuel_records (vehicle_id, refueled_at, mileage, fuel_amount_l, unit_price, total_cost, paid_amount, fuel_grade, station, fuel_type, is_full, note, created_at)
SELECT 2, '2026-03-06 13:23:00', NULL, 28.56, 7.53, 215.00, 206.00, '95', '中国石化安宁庄加油站', '汽油', 1, '', NOW()
WHERE NOT EXISTS (SELECT 1 FROM refuel_records WHERE vehicle_id=2 AND refueled_at='2026-03-06 13:23:00' AND station='中国石化安宁庄加油站');

INSERT INTO refuel_records (vehicle_id, refueled_at, mileage, fuel_amount_l, unit_price, total_cost, paid_amount, fuel_grade, station, fuel_type, is_full, note, created_at)
SELECT 2, '2026-01-19 11:25:00', NULL, 36.56, 7.14, 261.00, 246.00, '95', '中国石化安宁庄加油站', '汽油', 1, '', NOW()
WHERE NOT EXISTS (SELECT 1 FROM refuel_records WHERE vehicle_id=2 AND refueled_at='2026-01-19 11:25:00' AND station='中国石化安宁庄加油站');

INSERT INTO refuel_records (vehicle_id, refueled_at, mileage, fuel_amount_l, unit_price, total_cost, paid_amount, fuel_grade, station, fuel_type, is_full, note, created_at)
SELECT 2, '2025-12-12 12:29:00', NULL, 27.47, 7.28, 200.00, 200.00, '95', '中国石化天通苑加油站', '汽油', 1, '', NOW()
WHERE NOT EXISTS (SELECT 1 FROM refuel_records WHERE vehicle_id=2 AND refueled_at='2025-12-12 12:29:00' AND station='中国石化天通苑加油站');

INSERT INTO refuel_records (vehicle_id, refueled_at, mileage, fuel_amount_l, unit_price, total_cost, paid_amount, fuel_grade, station, fuel_type, is_full, note, created_at)
SELECT 2, '2025-10-30 13:38:00', NULL, 42.58, 7.28, 309.97, 279.97, '95', '中国石化北砖加油站', '汽油', 1, '', NOW()
WHERE NOT EXISTS (SELECT 1 FROM refuel_records WHERE vehicle_id=2 AND refueled_at='2025-10-30 13:38:00' AND station='中国石化北砖加油站');

INSERT INTO refuel_records (vehicle_id, refueled_at, mileage, fuel_amount_l, unit_price, total_cost, paid_amount, fuel_grade, station, fuel_type, is_full, note, created_at)
SELECT 2, '2025-10-03 10:16:00', NULL, 47.75, 7.57, 361.46, 361.46, '95', '中国石化北砖加油站', '汽油', 1, '', NOW()
WHERE NOT EXISTS (SELECT 1 FROM refuel_records WHERE vehicle_id=2 AND refueled_at='2025-10-03 10:16:00' AND station='中国石化北砖加油站');
