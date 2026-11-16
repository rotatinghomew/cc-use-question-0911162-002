全球南方治理参与席位与议程排程中心

运行验收：
python3 -m assembly_scheduler run --fixture fixtures/acceptance.json --database /tmp/assembly_scheduler.sqlite3 --output /tmp/assembly_scheduler-output

核验：
python3 -m assembly_scheduler verify --database /tmp/assembly_scheduler.sqlite3 --output /tmp/assembly_scheduler-output

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.representation_signal.test_representation_balance -v

构建检查：
python3 -m compileall -q assembly_scheduler tests
