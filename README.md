# Time Sync Monitoring to Zabbix

<div align="right">

[![日本語](https://img.shields.io/badge/Language-%E6%97%A5%E6%9C%AC%E8%AA%9E-blue.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

</div>

ntpd、Chrony、そして将来の PTP (Precision Time Protocol) による**時刻同期の品質・精度（オフセット、ジッター、遅延、到達性、Stratum 等）を測定・可視化・異常検知するための Zabbix 監視ツールセット & テンプレート**です。

---

## 🎯 プロジェクトの目的

時刻同期クライアント自体の動作設定ではなく、**「正しく・高精度に時刻が同期できているか」という同期品質を継続的にモニタリング**することを目的としています。

- **NTP アプライアンス / リモート NTP 監視**: エージェントを導入できない専用機器やルーター、リモート NTP サーバーの精度をリモートから低負荷で一括測定。
- **Chrony 監視**: Linux サーバー等のローカル Chrony デーモンの同期オフセット・周波数誤差・トラッキング状態を高精度に追跡。
- **PTP (将来対応予定)**: 金融・放送・高精度産業ネットワーク向けの IEEE 1588 PTP 同期品質監視。

---

## 🚀 対応予定アーキテクチャ

1. **Zabbix 7.0 / 6.0 LTS 対応テンプレート**: モダンなマスターアイテム & Dependent アイテム構成による低負荷設計。
2. **外部チェック（External check）& Agent 2 対応**: セキュリティ要件の厳しい環境でも `system.run` 不要で導入可能。
3. **AI-Setup-Ready (`AGENTS.md`)**: AI コーディングアシスタントによるゼロコンフィグ自動セットアップに対応。
