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

# mutation testing。mutmut 3.x は Python 3.10+ を要する。
# ローカルの本体が Python 3.9 の場合は専用 venv（.venv-mut）を作って使い、
# 本体が既に 3.10+ の環境（CI 等）では .venv をそのまま使う。
# （経緯は docs/case-study-02.md「環境上のつまずき」）
MUT_PY := $(shell [ -x .venv-mut/bin/python ] && echo .venv-mut/bin/python || echo .venv/bin/python)

# MUT_PY は Makefile 読み込み時に評価されるため、.venv-mut を作る前は
# .venv/bin/python に解決される。setup-mutation では明示的なパスを使う。
setup-mutation:
	python3.13 -m venv .venv-mut || python3 -m venv .venv-mut
	.venv-mut/bin/python -m pip install -q -r requirements.txt -r requirements-dev.txt mutmut

mutation: | $(REPORTS)
	$(MUT_PY) -m mutmut run
	python3 scripts/mutmut_to_json.py --python $(MUT_PY) --out $(REPORTS)/mutation.json

## ゲート -----------------------------------------------------------
JSIX := python3 ../../plugin/scripts/jsix_run_checks.py

# 内側ループ: 既にある成果物を読んで判定するだけ（コマンドは実行しない）
gate:
	$(JSIX)

# 外側ループ: コマンドを実行して成果物を作ってから判定する
gate-ci:
	$(JSIX) --run-commands --json $(REPORTS)/gate.json

clean:
	$(RM) -r $(REPORTS) coverage.xml .coverage .pytest_cache mutants
