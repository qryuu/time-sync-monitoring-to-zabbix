# Chrony 時刻同期監視 (Zabbix Template)

本ディレクトリは、`chronyd` を利用した時刻同期の高精度監視用 Zabbix テンプレートを格納しています。

## 構成
- `templates/template_chrony_accuracy_ja.yaml`: 日本語版テンプレート
- `templates/template_chrony_accuracy_en.yaml`: 英語版テンプレート

## 監視の特徴
- **高精度オフセット監視**: `chronyc tracking` によるナノ秒/マイクロ秒単位のシステムクロックオフセット（RMSオフセット、周波数誤差、Stratum）を監視。
- **動的ピア検出 (LLD)**: `chronyc sources` を解析し、現在同期中のアクティブマスター（`*`）およびスタンバイの上位NTPサーバー（`+`, `-`）を自動検出し、ピア別のオフセット・遅延・ジッターを個別監視。
- **実機検証済み**: Zabbix 7.0 LTS 上で実機検証・動作確認済み（エラー0件、全アイテム NORMAL）。

## Zabbix Agent 設定例 (`/etc/zabbix/zabbix_agent2.d/chrony.conf`)
```ini
UserParameter=chrony.tracking[*],chronyc tracking
UserParameter=chrony.sources[*],chronyc -c sources
```
