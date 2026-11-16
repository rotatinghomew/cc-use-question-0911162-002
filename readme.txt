全球南方治理参与席位与议程排程中心

运行验收：
python3 -m assembly_scheduler run --fixture fixtures/acceptance.json --database /tmp/assembly_scheduler.sqlite3 --output /tmp/assembly_scheduler-output

核验：
python3 -m assembly_scheduler verify --database /tmp/assembly_scheduler.sqlite3 --output /tmp/assembly_scheduler-output

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.representation_signal.test_representation_balance -v
python3 -m unittest tests.representation_audit.test_seat_plan -v
python3 -m unittest tests.confirmation.test_nomination_confirm -v
python3 -m unittest tests.domain.test_representation_audit_flow -v

构建检查：
python3 -m compileall -q assembly_scheduler tests

代表性缺口与替补（representation_audit）：
- fixtures/acceptance.json 的 allocation 块声明席位配额、低收入地区席位占比、专业目标和
  资格/时区/可用时段/容量四类硬性约束阈值。
- run 会在评分之外生成可核查的席位方案 seat-plan.json：每个未入选提名都带有排除原因，
  区分“硬性约束受阻”（含具体 blocker 证据）与“容量竞争落选”。
- representation-gaps.json 按低收入地区、地区组、专业三个维度对比目标席位数与实际席位，
  给出缺口、严重级别、受阻提名名单、约束归因以及可立即替补的提名；critical 表示不存在
  可行替补，warning 表示缺口由配额竞争造成。
- substitutions.json 只推荐通过全部硬性约束、且能填补公开缺口的提名，按可解释评分排序，
  并带稳定 substitution_id 接回提名确认流程。
- 同内容同时导出 CSV（seat-plan.csv、exclusions.csv、representation-gaps.csv、
  substitutions.csv），全部 JSON 产物进入 manifest 哈希核验。

提名确认与重新评估（confirmation / scheduler）：
- 确认通过：python3 -m assembly_scheduler confirm --database ... --record-id <id> \
    --outcome approved --reason "..." --output ...
  提名进入 confirmed，席位被钉住（pinned），后续任何无关候选变化都不能挤掉该席位。
- 确认拒绝：--outcome rejected 会把提名标记为 confirmation-rejected，立即触发席位方案
  重新评估，空出席位按替补建议自动回填，plan-diffs.json 记录增删与版本差异。
- 可用时段变化：python3 -m assembly_scheduler availability --database ... \
    --record-id <id> --window <数值> --output ...
  受影响提名按新窗口重新评估约束；已确认席位保持钉住，差异为零位移（displaced 为空）。
- 替补晋升：python3 -m assembly_scheduler promote --database ... \
    --substitution-id <id> --reason "..." --output ...
  校验替补仍可行后走同一确认流程，失效的 substitution_id 会被拒绝。
- 手动重新评估并导出：python3 -m assembly_scheduler plan --database ... --output ...
- 每次重新评估都会生成新版本席位方案、plan diff 与审计事件；sqlite 审计链与输出包哈希
  均可通过 verify 复核，inspect 可查看确认记录、当前方案与全部版本差异。
