# J-SIX 品質ゲート用のターゲット。
# `.jsix-checks.json` はここに書いたコマンド名と成果物のパスを宣言するだけで、
# plugin 側は成果物（JUnit XML / Cobertura / SARIF / mutation JSON）を読むだけ。
PY := .venv/bin/python
REPORTS := reports

.PHONY: setup build lint format sast test test-acceptance coverage mutation gate gate-ci clean

setup:
	python3 -m venv .venv
	$(PY) -m pip install -q -r requirements.txt -r requirements-dev.txt

$(REPORTS):
	@mkdir -p $(REPORTS)

## G1 ---------------------------------------------------------------
build:
	$(PY) -c "import compileall,sys; sys.exit(0 if compileall.compile_dir('app', quiet=1) else 1)"

lint:
	$(PY) -m ruff check app tests

format:
	$(PY) -m ruff format --check app tests

# bandit は指摘があると終了コード 1 を返すが、判定は SARIF を読む plugin 側で行う。
# ここでは SARIF が生成されたことだけを確認する。
sast: | $(REPORTS)
	-$(PY) -m bandit -q -r app -f sarif -o $(REPORTS)/sast.sarif
	@test -s $(REPORTS)/sast.sarif

## G2 ---------------------------------------------------------------
# 単体・結合テスト。hold-out は別ターゲット（GREEN 実装者に見せないため）
test: | $(REPORTS)
	$(PY) -m pytest tests --ignore=tests/acceptance -q \
		--junitxml=$(REPORTS)/junit.xml \
		--cov=app --cov-report=xml:coverage.xml --cov-report=term-missing

# hold-out 受入テスト（受入条件 UC-nnn 単位に最低1件）
test-acceptance: | $(REPORTS)
	$(PY) -m pytest tests/acceptance -q --junitxml=$(REPORTS)/junit-acceptance.xml

coverage: test

# mutation testing はケーススタディ #2 で導入する（実測してから閾値を決める）
mutation:
	@echo "mutation: 未導入（ケーススタディ #2 で実測してから閾値を決める）"

## ゲート -----------------------------------------------------------
JSIX := python3 ../../plugin/scripts/jsix_run_checks.py

# 内側ループ: 既にある成果物を読んで判定するだけ（コマンドは実行しない）
gate:
	$(JSIX)

# 外側ループ: コマンドを実行して成果物を作ってから判定する
gate-ci:
	$(JSIX) --run-commands --json $(REPORTS)/gate.json

clean:
	$(RM) -r $(REPORTS) coverage.xml .coverage .pytest_cache
