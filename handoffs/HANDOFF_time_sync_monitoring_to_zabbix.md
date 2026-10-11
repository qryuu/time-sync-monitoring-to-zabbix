# HANDOFF: time-sync-monitoring-to-zabbix 実機検証フィードバック完全反映

- **最終更新日時**: 2026-10-11 22:05 JST [固定PC]
- **対象タスク**: 実機検証（Zabbix 7.0.31 LTS on Amazon Linux 2023 ARM64）に基づく不具合対策・改善の完全反映とマージ

---

## 1. 完了した作業・決定事項

1. **Zabbix 7.0 スキーマ適合（全4点）**:
   - ルート直下の `date:` タグを完全削除（Issue 1 対策）。
   - ルート直下は `template_groups:`、各テンプレート内部のグループ所属参照は正規の `groups:` に修正（Issue 2 対策）。
   - `Templates/Applications` の UUID を公式の `a571c0d144b14fd4a87a9d9b2aa9fcd6` に統一（Issue 3 対策）。
   - ダッシュボードやLLDプロトタイプに残存していた連番風ダミーUUIDを、すべて正規の UUIDv4（`[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}`）に置換。既存の正規UUIDは保持してインポート互換性を担保（Issue 4 対策）。

2. **Chrony 4.x カラム仕様 & Zabbix `CSV_TO_JSON` 仕様適合（Issue 5 対策）**:
   - Zabbix の `CSV_TO_JSON(0)` は 1-based の文字列キー辞書 `[{"1":..., "2":...}]` を出力するため、JSONPath を `$[0]['6']` などの文字列キーに統一。
   - 実機 Chrony 4.3 の 14 カラム形式（Reference IP列含む）に合わせ、`Reference` (`$[0]['2']`), `Stratum` (`$[0]['3']`), `Systemtime` (`$[0]['5']`), `Lastoffset` (`$[0]['6']`), `RMSoffset` (`$[0]['7']`), `Rootdelay` (`$[0]['11']`), `Updateinterval` (`$[0]['13']`), `LeapStatus` (`$[0]['14']`) の抽出パスを正確に修正。

3. **超高精度環境（ns / us / ms / s）動的ミリ秒換算（Issue 6 対策）**:
   - AWS EC2 等の超高精度環境で出力される `ns` / `us` に対応するため、LLD の delay/offset アイテムに正規表現 `(ns|us|ms|s)` と前処理 JavaScript を実装。
   - 文字クラス内の不完全な16進エスケープ `\x` をリテラル文字 `x`（`[\*\+\-\?\~x]`）に是正。

4. **インポートスクリプトの安全性向上（Issue 7 対策）**:
   - `scripts/import_template.py` および `scripts/import_template.ps1` において、既存ホスト指定時に `selectParentTemplates` を取得し、既存テンプレート（OS監視等）を外さずに安全にマージする処理を追加。
   - ホスト検索で技術名（`host`）と表示名（`name`）のデュアル検索をサポート。

5. **CIテストスイート強化 & ドキュメント更新**:
   - `tests/test_template_validator.py` に `date` 不在、UUIDv4、テンプレート内 `groups`、正規グループUUIDの厳格テストを追加。
   - `tests/test_chrony_parsing.py` に Chrony 4.x 14カラム、Zabbix CSV_TO_JSON + JSONPath シミュレーション、LLD多単位換算のテストを追加。
   - `README.md` / `README_EN.md` にホスト表示名検索、安全マージ保護、エージェント再起動コマンド、超高精度環境対応の注記を追記。

6. **Pull Request & マージ完了**:
   - 作業ブランチ: `fix/hardware-verification-feedback`
   - PR: [#5](https://github.com/qryuu/time-sync-monitoring-to-zabbix/pull/5)
   - GitHub Actions CI (13/13件 PASS) を確認後、`main` ブランチへマージ完了。

---

## 2. 現在進行中の状態・直近のエラーや未完了課題

- **現在のGitブランチ**: `main` (最新に同期済み、working tree clean)
- **テスト状況**: `pytest` 13/13件 PASS
- **未完了課題**: なし。実機検証ログに記録された全8点の知見・不具合対策の反映および検証はすべて完了。

---

## 3. 次のPCで即座に着手すべき具体的TODO

1. **実機環境（Zabbix Server / EC2）での再インポート確認（任意）**:
   - 最新の `scripts/import_template.py` または `scripts/import_template.ps1` を用いて、修正済みテンプレートが最新の Zabbix 7.0 サーバーで警告なく上書きインポートできることを確認する。
2. **リリース（GitHub Release）の作成（必要に応じて）**:
   - 実機検証完了版として `v1.0.1` などのリリースタグを発行する。

---

## 4. 参照すべき主要ファイル・関連ドキュメント

- **実機検証ログ**: [C:\Users\housi\OneDrive\zabbix\TEMPLATE_VERIFICATION_LOG.md](file:///C:/Users/housi/OneDrive/zabbix/TEMPLATE_VERIFICATION_LOG.md)
- **日本語テンプレート**: [chrony/templates/template_chrony_accuracy_ja.yaml](file:///c:/Users/housi/OneDrive/ドキュメント/vscode/time-sync-monitoring-to-zabbix/chrony/templates/template_chrony_accuracy_ja.yaml)
- **インポートスクリプト**:
  - Python: [scripts/import_template.py](file:///c:/Users/housi/OneDrive/ドキュメント/vscode/time-sync-monitoring-to-zabbix/scripts/import_template.py)
  - PowerShell: [scripts/import_template.ps1](file:///c:/Users/housi/OneDrive/ドキュメント/vscode/time-sync-monitoring-to-zabbix/scripts/import_template.ps1)
- **テストコード**:
  - [tests/test_template_validator.py](file:///c:/Users/housi/OneDrive/ドキュメント/vscode/time-sync-monitoring-to-zabbix/tests/test_template_validator.py)
  - [tests/test_chrony_parsing.py](file:///c:/Users/housi/OneDrive/ドキュメント/vscode/time-sync-monitoring-to-zabbix/tests/test_chrony_parsing.py)
