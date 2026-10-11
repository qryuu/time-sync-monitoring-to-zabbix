# NTP (ntpd / ntpsec) 時刻同期監視

本ディレクトリは、`ntpd` または `ntpsec` を利用した時刻同期監視用 Zabbix テンプレート、および Agent レス（外部チェック）スクリプトを格納しています。

## 構成
- `templates/`: Zabbix テンプレート (`template_ntp_accuracy_ja.yaml`, `template_ntp_accuracy_en.yaml`)
- `scripts/`: Zabbix Agent を導入できない機器向けの外部チェックスクリプト (`zabbix_ntp_check.py`)

## 監視方式
1. **Zabbix Agent 方式 (`templates/`)**
   - `ntpq -pn` および `ntpq -c rv` を利用してローカルの `ntpd` / `ntpsec` デーモンの状態を詳細監視。
   - 動的ピア検出（LLD）により、アクティブマスター（`*`）とスタンバイサーバー（`+`, `-`）を自動検出し、ピア別のオフセット・遅延・ジッターをトラッキング。
2. **外部スクリプト方式 (`scripts/`)**
   - Python 標準ライブラリのみで動作する Agent レス NTP ポーリングスクリプト。
   - ルーター、スイッチ、監視対象外のアプライアンス等の NTP サーバーに対して直接パケットを送受信し、オフセット・RTT を計測。
