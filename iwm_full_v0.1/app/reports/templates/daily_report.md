# IWM 投资参谋日报 - {{date}}

## 1. 市场概况
| 市场 | 主要指数 | 涨跌 | 备注 |
|------|---------|------|------|
| A股 | {{a_share_index}} | {{a_share_change}} | {{a_share_note}} |
| 港股 | {{hk_index}} | {{hk_change}} | {{hk_note}} |
| 美股 | {{us_index}} | {{us_change}} | {{us_note}} |

**风险等级**: {{risk_level}}

## 2. 今日重点事件
{% for event in top_events %}
### {{loop.index}}. {{event.title}}
- **摘要**: {{event.summary}}
- **影响行业**: {{event.industries | join(', ')}}
- **影响级别**: {{event.impact_level}}/5
{% endfor %}

## 3. Agent委员会观点
{{committee_conclusion}}

## 4. 支持观点
{% for view in supporting_views %}
- {{view}}
{% endfor %}

## 5. 反对观点（Devil's Advocate）
{% for view in opposing_views %}
- ⚡ {{view}}
{% endfor %}

## 6. 风险提示
{% for risk in risk_warnings %}
- ⚠️ {{risk}}
{% endfor %}

## 7. 新发现机会
{% for opp in new_opportunities %}
- **{{opp.title}}** (评分: {{opp.score}}/100)
  - 逻辑: {{opp.logic}}
{% else %}
暂无新机会
{% endfor %}

---
*生成时间: {{generated_at}} | 置信度: {{confidence}}*
*本报告由IWM Agent委员会自动生成，仅供参考，不构成投资建议*
