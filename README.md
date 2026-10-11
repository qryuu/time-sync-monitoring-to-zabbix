# time-sync-monitoring-to-zabbix

<div align="right">

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![CI Test](https://github.com/qryuu/time-sync-monitoring-to-zabbix/actions/workflows/test.yml/badge.svg)](https://github.com/qryuu/time-sync-monitoring-to-zabbix/actions/workflows/test.yml)
[![日本語](https://img.shields.io/badge/Language-%E6%97%A5%E6%9C%AC%E8%AA%9E-blue.svg)](#)
[![English](https://img.shields.io/badge/Language-English-lightgrey.svg)](./README_EN.md)

</div>

Zabbix 7.0 / 6.0 LTS 対応の高精度時刻同期監視テンプレートスイートです。  
NTP（ntpd）、Chrony、PTP（linuxptp / IEEE 1588）、およびリモートNTPアプライアンス（Agentless / External check）の時刻精度・同期品質を包括的に可視化・監視します。

> [!TIP]
> **🤖 AI コーディングアシスタントをご利用の場合 (AI-setup-ready)**:  
> Antigravity, Cursor, Claude Code, GitHub Copilot などの AI アシスタントに対して**「このリポジトリをセットアップして」**と伝えるだけで、対話形式で環境判定・動作テスト・テンプレートインポートまで自動完了します。詳細は [`AGENTS.md`](./AGENTS.md) をご覧ください。

---

## 主な特徴

1. **マスターアイテム化による負荷 1/8 削減**:
   - `ntpq`、`chronyc`、`pmc` の実行を 1 つのマスターアイテムに集約。
   - 監視対象およびエージェントのプロセス・ネットワーク負荷を劇的に削減し、全メトリクスを完全同一瞬間の値（アトミック性）として記録。
2. **LLD（ローレベルディスカバリ）による全同期サーバー自動監視（Chrony & NTP 双方対応）**:
   - 現在アクティブな同期先（マスター）だけでなく、設定されている予備サーバー・全ピア（スタンバイ候補、外れ値、不良サーバー）を自動検出。
   - サーバーごとの遅延（Delay）、オフセット、ジッター（Jitter）、到達性（Reachability）、同期役割（Sync Status）を個別追跡し、予備サーバーのサイレントダウンを早期検知。
3. **PTP (IEEE 1588 / linuxptp) マイクロ秒・ナノ秒高精度監視**:
   - `linuxptp` (`ptp4l`, `phc2sys`, `pmc`) に完全対応。
   - マスターオフセット (ns)、平均経路遅延 (ns)、グランドマスター検知状態、ポート状態（SLAVE/MASTER）、プロセス稼働を包括監視。
4. **Grafana風モダンSVG集約ダッシュボード**:
   - Zabbix 7.0 標準の `type: svggraph` と `type: item`（カード型単一値）を採用。
   - クライアントのシステム時刻オフセット推移（半透明グラデーション塗りつぶし）と、全同期サーバーの遅延オーバーレイ比較を一画面で可視化。
5. **エージェント不要の外部チェック（Agentless / External check）対応**:
   - Python標準ライブラリのみで動作する高精度NTP測定スクリプト `ntp/scripts/zabbix_ntp_check.py` を同梱。
   - アプライアンスやネットワークスイッチなど、Zabbix Agentを導入できない機器も直接監視可能。
6. **最初から日英バイリンガル対応（`_ja.yaml` / `_en.yaml`）**:
   - インポートスクリプト（PowerShell / Python）がOS言語を自動判別して適切なテンプレートを展開。

---

## ディレクトリ構成

```text
time-sync-monitoring-to-zabbix/
├── chrony/
│   ├── README.md                             # Chrony 監視仕様
│   └── templates/
│       ├── template_chrony_accuracy_ja.yaml  # 日本語版テンプレート
│       └── template_chrony_accuracy_en.yaml  # 英語版テンプレート
├── ntp/
│   ├── README.md                             # NTP 監視仕様
│   ├── templates/
│   │   ├── template_ntp_accuracy_ja.yaml     # 日本語版テンプレート（ローカル＆リモート）
│   │   └── template_ntp_accuracy_en.yaml     # 英語版テンプレート
│   └── scripts/
│       └── zabbix_ntp_check.py               # 外部チェック用スクリプト
├── ptp/
│   ├── README.md                             # PTP (IEEE 1588) 監視仕様
│   └── templates/
│       ├── template_ptp_accuracy_ja.yaml     # 日本語版テンプレート (linuxptp)
│       └── template_ptp_accuracy_en.yaml     # 英語版テンプレート (linuxptp)
├── scripts/
│   ├── import_template.ps1                   # Zabbix APIインポート（PowerShell）
│   └── import_template.py                    # Zabbix APIインポート（Python）
├── tests/                                    # 単体テスト ＆ YAML規約バリデータ
├── AGENTS.md                                 # AI協働セットアップ規約
├── README.md                                 # 本ドキュメント（日本語）
├── README_EN.md                              # 英語ドキュメント
└── LICENSE                                   # MIT License
```

---

## クイックスタート

### 1. Zabbix Web へのインポート

#### PowerShell を使用する場合:
```powershell
.\scripts\import_template.ps1 -ZabbixUrl "http://zabbix-server/zabbix" -ApiToken "<YOUR_API_TOKEN>" -TemplateType Chrony -HostName "Web-Server-01"
```

#### Python を使用する場合:
```bash
python scripts/import_template.py --url "http://zabbix-server/zabbix" --token "<YOUR_API_TOKEN>" --type chrony --host "Web-Server-01"
```

> [!NOTE]
> - **ホスト名の柔軟な指定**: `--host` / `-HostName` には、Zabbix上の技術名（Host name）または表示名（Visible name）のいずれも指定可能です。
> - **既存テンプレートの保護（安全マージ）**: 既存ホストを指定した場合、すでにリンクされているOS監視やミドルウェアのテンプレートを解除することなく、本テンプレートを追加マージします。
> - **新規ホストの自動作成**: 指定したホストが Zabbix 上に存在しない場合は、`host.create` により自動作成されて安全にリンクされます。

### 2. エージェント側の設定確認
`zabbix_agentd.conf` または `zabbix_agent2.conf` で以下が有効になっていることを確認してください：
```ini
AllowKey=system.run[*]
```
設定変更後はエージェントサービスを再起動してください：
```bash
sudo systemctl restart zabbix-agent # または zabbix-agent2
```

> [!TIP]
> **超高精度環境 & Chrony 4.x に完全対応**:  
> AWS EC2（Amazon Time Sync Service: `169.254.169.123`）など、ナノ秒（`ns`）やマイクロ秒（`us`）で同期する環境でも自動換算され、正常に記録されます。Chrony 4.x の 14 カラム出力にも完全対応しています。

---

## 収集メトリクス一覧

| メトリクス名 | 説明 | 収集方式 |
| :--- | :--- | :--- |
| **System time offset** | システムクロックとNTPマスター間の時刻ズレ（ms） | マスター / 依存アイテム |
| **RMS offset** | 長期平均オフセット（ms） | マスター / 依存アイテム |
| **Root delay** | 最上位Stratum-1サーバーまでの合計往復遅延時間（ms） | マスター / 依存アイテム |
| **Stratum** | 階層レベル（Stratum 1〜16） | マスター / 依存アイテム |
| **Leap status** | 閏秒挿入/削除および同期状態 | マスター / 依存アイテム |
| **NTP source Reachability** | 各同期先サーバーの到達性レジスタ値（過去8回） | LLD / 依存アイテム |
| **NTP source Delay / Offset** | 各同期先サーバー個別の推定遅延およびオフセット | LLD / 依存アイテム |

---

## ライセンス
[MIT License](LICENSE)
