# PTP (Precision Time Protocol / IEEE 1588) 時刻同期監視

本ディレクトリは、PTP (IEEE 1588-2008 / PTPv2) の `linuxptp` (`ptp4l`, `phc2sys`, `pmc`) 高精度時刻同期（マイクロ秒〜ナノ秒単位）の監視テンプレートおよび仕様を管理します。

## 構成
- `templates/template_ptp_accuracy_ja.yaml`: 日本語版テンプレート
- `templates/template_ptp_accuracy_en.yaml`: 英語版テンプレート

## PTP の代表的なデーモンとアーキテクチャ (`linuxptp`)
Linux 環境における事実上の標準実装は **`linuxptp`** パッケージです。主に以下のデーモンおよびツールで構成されます。

1. **`ptp4l` (PTP for Linux デーモン)**
   - PTP 通信プロトコル本体を実行するデーモン。
   - ネットワーク上のグランドマスタークロック（GM）と PTP パケットをやり取りし、**NIC（ネットワークカード）内のハードウェアクロック (PHC: PTP Hardware Clock)** をナノ秒精度で同期します。
   - `systemd`: `ptp4l.service`

2. **`phc2sys` (PHC to System デーモン)**
   - NIC のハードウェアクロック（PHC）の時刻を、**OS のシステムクロック (`CLOCK_REALTIME`)** へリアルタイムに同期・転写するデーモン。
   - `systemd`: `phc2sys.service`

3. **`pmc` (PTP Management Client)**
   - PTP デーモンの稼働状態、ポート状態（Master/Slave/Passive）、グランドマスターID、オフセット値等を照会する CLI（`chronyc` や `ntpq` に相当）。
   - 本テンプレートは、`pmc` からの一括照会結果を Zabbix 側で JSON 前処理（JavaScript）により高速・高精度にパースして監視します。

4. **`timemaster`**
   - NTP (`chronyd`) と PTP (`ptp4l`) を協調動作させ、PTP 障害時に NTP へフォールバックする統合制御デーモン。

---

## 監視項目一覧

| アイテム名 | キー | 単位 | 説明 |
| :--- | :--- | :---: | :--- |
| **マスターオフセット** | `ptp.offset_from_master` | ns | グランドマスターとの時刻偏差 (ナノ秒) |
| **平均経路遅延** | `ptp.mean_path_delay` | ns | マスター/スレーブ間の平均ネットワーク往復遅延の片道分 |
| **GM 検知状態** | `ptp.gm_present` | - | グランドマスターが存在するかどうか (`true`/`false`) |
| **ポート状態** | `ptp.port_state` | - | PTP ポートのステータス (`SLAVE`, `MASTER`, `LISTENING` 等) |
| **グランドマスター ID** | `ptp.gm_identity` | - | 同期中グランドマスターのクロック識別子 (EUI-64) |
| **ステップ数 (ホップ数)** | `ptp.steps_removed` | - | グランドマスターからのバウンダリクロック段数 |
| **ポート ID** | `ptp.port_identity` | - | ローカル PTP ポート識別子 |
| **ptp4l プロセス数** | `proc.num[ptp4l]` | - | `ptp4l` デーモンの稼働監視 |
| **phc2sys プロセス数** | `proc.num[phc2sys]` | - | `phc2sys` デーモンの稼働監視 |

---

## 設定手順 (Zabbix Agent)

### 1. リモートコマンドの許可 (推奨)
`/etc/zabbix/zabbix_agent2.conf` (または `zabbix_agentd.conf`) に以下を設定します:
```ini
AllowKey=system.run[*]
```

### 2. UserParameter を使用する場合
リモートコマンドを全許可しない場合は、以下の設定ファイルを作成します (`/etc/zabbix/zabbix_agent2.d/ptp.conf`):
```ini
UserParameter=ptp.pmc.raw[*],pmc -u -b 0 'GET TIME_STATUS_NP' 'GET CURRENT_DATA_SET' 'GET PORT_DATA_SET'
```

※ `pmc` が接続する Unix ドメインソケット (`/var/run/ptp4l`) に `zabbix` ユーザーがアクセスできるよう、必要に応じてパーミッションまたはグループ権限（例: `usermod -aG <group> zabbix`）を調整してください。
