# IWM 机会扫描报告 - {{date}}

## 扫描概览
- **扫描日期**: {{date}}
- **发现机会数**: {{opportunities | length}}
- **最高评分**: {% if opportunities %}{{ (opportunities | sort(attribute='score', reverse=True))[0].score }}/100{% else %}N/A{% endif %}
- **整体市场情绪**: {{market_sentiment | default('中性')}}

---

## 机会详情
{% for opp in opportunities %}
### {{loop.index}}. {{opp.title}}
| 维度 | 详情 |
|------|------|
| **行业** | {{opp.industry}} |
| **触发逻辑** | {{opp.trigger_logic}} |
| **评分** | {{opp.score}}/100 |
| **置信度** | {{opp.confidence | default('N/A')}} |
| **时间框架** | {{opp.timeframe | default('未指定')}} |

**证据链**:
{% for evidence in opp.evidence_list %}
- {{evidence}}
{% endfor %}

**反方观点**:
{% for counter in opp.counter_arguments %}
- ⚡ {{counter}}
{% else %}
- 暂无明确反方观点
{% endfor %}

**建议行动**: {{opp.suggested_action | default('继续观察')}}

---
{% else %}
### 本次扫描未发现显著机会

可能的原因：
- 市场处于震荡整理期，缺乏明确方向
- 数据覆盖率不足
- 阈值设置过高

建议关注宏观数据更新及新闻动态。
{% endfor %}

## 行业热力图
{% for industry in industry_heatmap %}
- {{industry.name}}: {{industry.score}}/100 ({{industry.trend | default('→')}})
{% endfor %}

---
*生成时间: {{generated_at}}*
*本报告由IWM Agent委员会自动生成，仅供参考，不构成投资建议*
