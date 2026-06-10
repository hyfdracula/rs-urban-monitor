"""
一次性脚本：导出 FAO GAUL 中国全部区县的 ADM2_CODE + ADM2_NAME
运行方式：python export_gaul_districts.py
输出：gaul_china_districts.json（约 2850 条记录）
"""

import json
import ee
import tempfile
import os

# 从数据库读取用户的 GEE 密钥（和后端一样的初始化方式）
from app.database import get_db_context
from app.models import UserGEEKey


def main():
    # 1. 获取一个有效的 GEE 密钥
    with get_db_context() as db:
        key_record = db.query(UserGEEKey).first()
        if not key_record:
            print("ERROR: 数据库里没有任何 GEE 密钥，请先在网页上配置")
            return
        print(f"使用密钥: {key_record.service_account} (status={key_record.status})")

        # 解密密钥
        from app.gee_key_service import gee_key_service
        service_account = key_record.service_account
        key_json = gee_key_service._decrypt(key_record.encrypted_key)

    # 2. 初始化 GEE
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(key_json)
        key_path = f.name

    try:
        credentials = ee.ServiceAccountCredentials(service_account, key_path)
        ee.Initialize(credentials)
        print("GEE 初始化成功")

        # 3. 查询中国所有 GAUL level2 区县
        gaul = ee.FeatureCollection("FAO/GAUL/2015/level2")
        china = gaul.filter(ee.Filter.eq('ADM0_NAME', 'China'))

        # 4. 获取所有要素的属性
        features = china.getInfo()["features"]
        print(f"找到 {len(features)} 个中国区县")

        # 5. 提取 ADM2_CODE + ADM2_NAME + ADM1_NAME（省份）
        districts = []
        for feat in features:
            props = feat.get("properties", {})
            districts.append({
                "adm2_code": props.get("ADM2_CODE"),
                "adm2_name": props.get("ADM2_NAME"),
                "adm1_name": props.get("ADM1_NAME"),  # 省份名（拼音）
                "adm1_code": props.get("ADM1_CODE"),
            })

        # 6. 按 ADM2_CODE 排序
        districts.sort(key=lambda x: x["adm2_code"])

        # 7. 输出 JSON
        out_path = os.path.join(os.path.dirname(__file__), "gaul_china_districts.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(districts, f, ensure_ascii=False, indent=2)

        print(f"已保存到: {out_path}")
        print(f"\n前 5 条示例:")
        for d in districts[:5]:
            print(f"  {d['adm2_code']}: {d['adm2_name']} ({d['adm1_name']})")

    finally:
        os.unlink(key_path)


if __name__ == "__main__":
    main()