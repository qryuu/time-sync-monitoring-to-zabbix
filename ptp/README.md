# PTP (Precision Time Protocol / IEEE 1588) 時刻同期監視

本ディレクトリは、PTP (IEEE 1588-2008 / PTPv2) 高精度時刻同期（マイクロ秒〜ナノ秒単位）の監視仕様およびテンプレートを管理します。

## PTP の代表的なデーモンとアーキテクチャ (`linuxptp`)
Linux 環境における事実上の標準実装は **`linuxptp`** パッケージです。主に以下のデーモンおよびツールで構成されます。

1. **`ptp4l` (PTP for Linux デーモン)**
   - PTP 通信プロトコル本体を実行するデーモン（httpd や chronyd に相当）。
   - ネットワーク上のグランドマスタークロック（GM）と PTP パケットをやり取りし、**NIC（ネットワークカード）内のハードウェアクロック (PHC: PTP Hardware Clock)** をナノ秒精度で同期します。
   - `systemd`: `ptp4l.service`

2. **`phc2sys` (PHC to System デーモン)**
   - NIC のハードウェアクロック（PHC）の時刻を、**OS のシステムクロック (`CLOCK_REALTIME`)** へリアルタイムに同期・転写するデーモン。
   - `systemd`: `phc2sys.service`

3. **`pmc` (PTP Management Client)**
   - PTP デーモンの稼働状態、ポート状態（Master/Slave/Passive）、グランドマスターID、オフセット値等を照会する CLI（`chronyc` や `ntpq` に相当）。
   - Zabbix 等の監視エージェントはこの `pmc` 経由でメトリクスを収集します。

4. **`timemaster`**
   - NTP (`chronyd`) と PTP (`ptp4l`) を協調動作させ、PTP 障害時に NTP へフォールバックする統合制御デーモン。

## 今後のロードマップ
- `ptp4l` のポート状態（Master, Slave, Faulty 等）およびオフセット監視テンプレート
- `phc2sys` のシステムクロック追従オフセット監視
- `pmc` を利用した UserParameter 定義の提供
