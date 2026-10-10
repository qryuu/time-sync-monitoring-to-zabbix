# HANDOFF: time-sync-monitoring-to-zabbix

## 1. 基本メタデータ
- **最終更新日時**: 2026-10-11 01:55:00 (JST)
- **発信元環境**: Windows 11 (PowerShell 7 / pwsh)
- **対象プロジェクト**: `time-sync-monitoring-to-zabbix`
- **リポジトリURL**: https://github.com/qryuu/time-sync-monitoring-to-zabbix
- **ローカル作業パス**: `c:\Users\housi\OneDrive\ドキュメント\vscode\time-sync-monitoring-to-zabbix`
- **Author**: @qryuu

---

## 2. 完了した作業・決定事項
- **リポジトリ新設**:
  - 時刻同期そのものではなく「同期の品質・精度を測定・監視する」という役割を明確化した `time-sync-monitoring-to-zabbix` リポジトリを新規作成。
  - MIT License、`.gitignore`、初期 `README.md` を含めて GitHub リモートへプッシュ完了。
- **プロジェクトスコープの決定**:
  - ntpd、Chrony を対象とし、将来的に PTP (Precision Time Protocol) の拡張も視野に入れた統合構成とする。
- **Zabbix コミュニティ公式アセットの精査完了**:
  - 過去に寄稿された `Applications/NTP/template_ntp_accuracy_japanese/6.0/` および `template_chrony_accuracy_japanese/6.0/` の仕様を確認済み。

---

## 3. ★重要：実機AIテストから得られた設計・実装上の注意点 (Lessons Learned)
Speedtest の別マシン実機セットアップ検証で得られた知見を、本プロジェクトの初期設計に最初から組み込むこと：

1. **ホスト未登録時の自動作成 (`host.create`) & AIの既存ホスト誤用防止**:
   - `import_template.ps1` / `.py` を作成する際は、最初から「指定されたホストが存在しない場合に `host.create` でホストを自動作成してリンクする」ロジックを実装すること。
   - `AGENTS.md` のプロトコルに「指定ホストが Zabbix 上に存在しない場合でも、無関係な既存ホスト（過去のテストホスト等）を勝手に探したり再利用してはならない」という禁止ルールを明記すること。
2. **外部コマンド未配置時の自律インストールの許容**:
   - `ntpq` や `chronyc` が対象環境に未インストールの場合、ユーザーへの手動案内を挟む前に、AI がパッケージマネージャー（`apt`, `dnf`, `winget` 等）で自律的にインストール・疎通テストを行えるプロトコルを規定すること。
3. **Zabbix 7.0 構文・定数・命名規則の厳格準拠**:
   - **グラフ描画タイプ**: 必ず `SINGLE_LINE` を使用すること（`LINE` は Zabbix 7.0 で `unexpected constant` エラーになる）。
   - **API パラメータ名**: `configuration.import` の `rules` は、キャメルケースの `templateDashboards` を使用すること（`template_dashboards` はエラー）。
   - **テンプレート技術名のプレフィックス**: ホスト名との重複衝突（`Host with host name "xxx" already exists`）を回避するため、`template: template_ntp_accuracy`, `template: template_chrony_accuracy` のように必ず `template_` プレフィックスを付与すること。

---

## 4. 現在進行中の状態 & 課題
- **リポジトリ状態**:
  - `main` ブランチのみ（初期コミット完了直後のクリーンな状態）。
- **直近の課題**:
  1. 過去の 6.0 テンプレートの取り込み（ベースライン設定）。
  2. `ntp` 側のマスターアイテム化（1回の `ntpq` 実行で全Dependentアイテム展開、ネットワーク負荷 1/8 削減）。
  3. `ntp` 側の外部チェック（External check / Agentless）スクリプトの作成（`zabbix_ntp_check.py` 等）。
  4. `chrony` 側の `-c`（CSV出力）による前処理シンプル化およびマクロ（`{$NTP_OFFSET_SMALL}`）の整合性修正。
  5. Zabbix 7.0 対応（`template_groups` 構文の適用、`SINGLE_LINE` 徹底）。
  6. AI-setup-ready（`AGENTS.md`）および日英ドキュメント（`README.md`, `README_EN.md`）の整備。

---

## 5. 次の会話で即座に着手すべき具体的 TODO（優先度順）

1. **トピックブランチ作成**:
   - `git checkout -b feat/import-and-modernize-templates`
2. **ディレクトリ構造の作成**:
   ```text
   time-sync-monitoring-to-zabbix/
   ├── ntp/
   │   ├── templates/
   │   │   └── template_ntp_accuracy.yaml
   │   └── scripts/
   │       └── zabbix_ntp_check.py
   ├── chrony/
   │   ├── templates/
   │   │   └── template_chrony_accuracy.yaml
   │   └── scripts/
   ├── ptp/
   │   └── README.md
   ├── AGENTS.md
   ├── README.md
   ├── README_EN.md
   └── LICENSE
   ```
3. **過去アセットの移植 & 現代化**:
   - `community-templates/Applications/NTP/template_ntp_accuracy_japanese/6.0/` からの移植とマスターアイテム化。
   - `community-templates/Applications/NTP/template_chrony_accuracy_japanese/6.0/` からの移植と前処理改善。
4. **外部チェックスクリプトの実装**:
   - Python / Shell スクリプトによるリモート NTP サーバー / アプライアンスの低負荷・アトミック測定。
5. **AI セットアップ対応 (`AGENTS.md`)**:
   - 環境判定、エージェント設定確認（`AllowKey=system.run[*]` 等）、動作テストウィザードの定義。
   - 注意点に挙げた「CLI自律インストール許可」「ホスト誤用禁止」ルールを包含。
6. **テスト・レビュー & PR 作成**:
   - TypeSafe AI (Jev) / Pro モデルレビューを行い、GitHub PR で `main` へマージ。
   - その後、Zabbix 公式（`zabbix/community-templates`）への寄稿 PR を作成。

---

## 6. 参照すべき主要ファイル・関連リソース
- **本リポジトリ**: `c:\Users\housi\OneDrive\ドキュメント\vscode\time-sync-monitoring-to-zabbix`
- **過去の公式テンプレート参照元**:
  - `c:\Users\housi\OneDrive\ドキュメント\vscode\community-templates\Applications\NTP\template_ntp_accuracy_japanese\6.0\`
  - `c:\Users\housi\OneDrive\ドキュメント\vscode\community-templates\Applications\NTP\template_chrony_accuracy_japanese\6.0\`
- **参考（直前で完了した PR）**:
  - `c:\Users\housi\OneDrive\ドキュメント\vscode\speeadtest_bat\` (Speedtest プロジェクト構成・v1.0.1 修正差分)
  - https://github.com/zabbix/community-templates/pull/863 (公式 PR #863)
