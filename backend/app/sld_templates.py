"""
GeoServer SLD 样式模板
===================
自动为不同图层应用配色方案。
"""

from __future__ import annotations

# ──────────────────────────────────────────────
# RSEI 色带样式（0~1，越高越绿）
# ──────────────────────────────────────────────

RSEI_SLD = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ColorMap type="ramp">
              <ColorMapEntry color="#000000" quantity="-9999" opacity="0" />
              <ColorMapEntry color="#D7191C" label="0.0" quantity="0.0" />
              <ColorMapEntry color="#FDAE61" label="0.25" quantity="0.25" />
              <ColorMapEntry color="#FFFFBF" label="0.5" quantity="0.5" />
              <ColorMapEntry color="#A6D96A" label="0.75" quantity="0.75" />
              <ColorMapEntry color="#1A9641" label="1.0" quantity="1.0" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

# ──────────────────────────────────────────────
# RSEI 等级分类样式（优/良/中/差）
# ──────────────────────────────────────────────

RSEI_CLASS_SLD = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <Title>差 (&lt;0.4)</Title>
          <RasterSymbolizer>
            <ColorMap type="values">
              <ColorMapEntry color="#D7191C" quantity="1" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
        <Rule>
          <Title>中 (0.4-0.6)</Title>
          <RasterSymbolizer>
            <ColorMap type="values">
              <ColorMapEntry color="#FDAE61" quantity="2" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
        <Rule>
          <Title>良 (0.6-0.8)</Title>
          <RasterSymbolizer>
            <ColorMap type="values">
              <ColorMapEntry color="#A6D96A" quantity="3" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
        <Rule>
          <Title>优 (&gt;0.8)</Title>
          <RasterSymbolizer>
            <ColorMap type="values">
              <ColorMapEntry color="#1A9641" quantity="4" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

# ──────────────────────────────────────────────
# 建设用地样式（红/橙/黄）
# ──────────────────────────────────────────────

BUILT_SLD = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ColorMap type="values">
              <ColorMapEntry color="#000000" quantity="0" label="非建设用地" opacity="0.0" />
              <ColorMapEntry color="#FF6B6B" quantity="1" label="建设用地" opacity="0.85" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

# ──────────────────────────────────────────────
# 新增建设用地样式（高亮红）
# ──────────────────────────────────────────────

NEW_BUILT_SLD = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ColorMap type="values">
              <ColorMapEntry color="#000000" quantity="0" label="非新增建设用地" opacity="0.0" />
              <ColorMapEntry color="#FF0000" quantity="1" label="新增建设用地" opacity="0.9" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

# ──────────────────────────────────────────────
# NDVI 色带样式
# ──────────────────────────────────────────────

NDVI_SLD = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ColorMap type="ramp">
              <ColorMapEntry color="#000000" quantity="-9999" opacity="0" />
              <ColorMapEntry color="#FFFFFF" label="-0.2" quantity="-0.2" />
              <ColorMapEntry color="#D7C5A0" label="0.0" quantity="0.0" />
              <ColorMapEntry color="#BEDE8B" label="0.2" quantity="0.2" />
              <ColorMapEntry color="#5EAA4A" label="0.4" quantity="0.4" />
              <ColorMapEntry color="#1E6B31" label="0.6" quantity="0.6" />
              <ColorMapEntry color="#004D18" label="0.8" quantity="0.8" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

# ──────────────────────────────────────────────
# 夜灯样式（暗→亮黄→白）
# ──────────────────────────────────────────────

NIGHTLIGHT_SLD = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ColorMap type="ramp">
              <ColorMapEntry color="#000000" quantity="-9999" opacity="0" />
              <ColorMapEntry color="#000000" label="0" quantity="0" opacity="0" />
              <ColorMapEntry color="#332200" label="5" quantity="5" />
              <ColorMapEntry color="#664400" label="15" quantity="15" />
              <ColorMapEntry color="#CC8800" label="30" quantity="30" />
              <ColorMapEntry color="#FFCC00" label="50" quantity="50" />
              <ColorMapEntry color="#FFFFFF" label="80" quantity="80" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

# ──────────────────────────────────────────────
# LST 地表温度样式（蓝→绿→黄→红）
# ──────────────────────────────────────────────

LST_SLD = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ColorMap type="ramp">
              <ColorMapEntry color="#000000" quantity="-9999" opacity="0" />
              <ColorMapEntry color="#2B3990" label="5" quantity="5" />
              <ColorMapEntry color="#3F8EB0" label="15" quantity="15" />
              <ColorMapEntry color="#7EC87E" label="25" quantity="25" />
              <ColorMapEntry color="#FEE661" label="35" quantity="35" />
              <ColorMapEntry color="#E6371E" label="45" quantity="45" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

# ──────────────────────────────────────────────
# 人口样式（浅→深紫）
# ──────────────────────────────────────────────

POPULATION_SLD = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ColorMap type="ramp">
              <ColorMapEntry color="#000000" quantity="-9999" opacity="0" />
              <ColorMapEntry color="#F2F0F7" label="0" quantity="0" opacity="0" />
              <ColorMapEntry color="#DADAEB" label="10" quantity="10" />
              <ColorMapEntry color="#9E9AC8" label="30" quantity="30" />
              <ColorMapEntry color="#6A51A3" label="60" quantity="60" />
              <ColorMapEntry color="#3F007D" label="100" quantity="100" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

# ──────────────────────────────────────────────
# GDP 人均收入样式（浅黄→橙→红，PPP USD）
# ──────────────────────────────────────────────

GDP_SLD = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ColorMap type="ramp">
              <ColorMapEntry color="#000000" quantity="-9999" opacity="0" />
              <ColorMapEntry color="#FFFFCC" label="0" quantity="0" opacity="0" />
              <ColorMapEntry color="#FFEDA0" label="5000" quantity="5000" />
              <ColorMapEntry color="#FEB24C" label="15000" quantity="15000" />
              <ColorMapEntry color="#FC4E2A" label="30000" quantity="30000" />
              <ColorMapEntry color="#E31A1C" label="60000" quantity="60000" />
              <ColorMapEntry color="#800026" label="100000" quantity="100000" />
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""


# ──────────────────────────────────────────────
# 样式映射表（精确匹配，向后兼容）
# ──────────────────────────────────────────────

SLD_MAP: dict[str, str] = {
    "rsei_2020": RSEI_SLD,
    "rsei_class_2020": RSEI_CLASS_SLD,
    "built_2000": BUILT_SLD,
    "built_2018": BUILT_SLD,
    "new_built": NEW_BUILT_SLD,
    "ndvi_2020": NDVI_SLD,
    "lst_2020": LST_SLD,
    "viirs_2020": NIGHTLIGHT_SLD,
    "population_2020": POPULATION_SLD,
    "gdp_2020": GDP_SLD,
}

# ──────────────────────────────────────────────
# 前缀匹配表（支持动态年份，如 rsei_2010, built_2020 等）
# ──────────────────────────────────────────────

_PREFIX_MAP: list[tuple[str, str]] = [
    # 注意：长前缀优先匹配（rsei_class_ 在 rsei_ 之前）
    ("rsei_class_", RSEI_CLASS_SLD),
    ("rsei_", RSEI_SLD),
    ("built_", BUILT_SLD),
    ("new_built", NEW_BUILT_SLD),
    ("ndvi_", NDVI_SLD),
    ("lst_", LST_SLD),
    ("viirs_", NIGHTLIGHT_SLD),
    ("ntl_", NIGHTLIGHT_SLD),
    ("population_", POPULATION_SLD),
    ("gdp_", GDP_SLD),
]


def get_sld(layer_type: str, layer_name: str) -> str | None:
    """获取图层对应的 SLD 样式。

    支持两种匹配方式：
      1. 前缀匹配（rsei_2010, built_2020 等动态年份）
      2. 精确匹配（向后兼容旧 key）

    Args:
        layer_type: 图层类型 (rsei_2020, built_2010, new_built 等)
        layer_name: GeoServer 中的图层名

    Returns:
        SLD XML 字符串，如果没有对应样式则返回 None
    """
    # 1. 前缀匹配
    for prefix, template in _PREFIX_MAP:
        if layer_type.startswith(prefix) or layer_type == prefix.rstrip("_"):
            return template.format(layer_name=layer_name)

    # 2. 精确匹配（向后兼容）
    template = SLD_MAP.get(layer_type)
    if template:
        return template.format(layer_name=layer_name)

    return None
