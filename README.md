# ikegam1-3dprint-data

3Dプリント用のデータ置き場です。

## プロジェクト

- [molkkaari](molkkaari/)：モルッカーリ本体・3.5m測定具の試作版・純正木製品用角度カバー・旧版延長ジョイント。STL・設計ソース・組立イメージ図・説明書。
- [measure-3p5m](measure-3p5m/)：3.5m測定具の新しい連結方式の試作記録（v13など）。**実機試験中・完成版ではありません。**
- [molkky_trophy](molkky_trophy/)：モルックトロフィー（おおみそCUP / 横浜鶴見モルック会）。

## 印刷前の注意

- 各フォルダの README に記載したバージョン・状態・必要な印刷枚数を確認してください。
- **試作・未検証のSTLがあります。** 特に測定具の回転ジョイントは、過去版で折損や連結不良がありました。まず短い試験片を印刷してください。
- Flashforge Adventurer 5M の造形範囲は 220×220×220mm です。スライサーで向き・サポート・サイズを確認してください。

## モルッカーリ・3.5m測定具の試作と印刷設定

- [TPU95A モルッカーリ v3.0 推奨印刷設定](molkkaari/TPU95A_v3_4parts/PRINT_SETTINGS.md) — 4分割・一体ジョイント。0.4mmノズルを想定。実機での嵌合は未検証。
- [TPU95A 3.5m測定具 v13 試験用 推奨印刷設定](measure-3p5m/TPU95A_v13_print_in_place_test/PRINT_SETTINGS.md) — 0.8mmノズル用、**2節／3節のみの試験**。3.5m完成版ではありません。
- [TPU95Aの途中詰まり対策と設定](docs/TPU95A_STABLE_PRINTING_AD5M.md) — Adventurer 5M向け。
- [測定具 v9〜v12 の不具合履歴と注意](measure-3p5m/previous-prototypes/PRINT_SETTINGS.md) — 旧版は本番印刷非推奨。

**ご注意：これらの設計は試作です。** モルッカーリの結合強度、測定具の直進性・3,500mm精度・収納性は実機での検証を要します。
