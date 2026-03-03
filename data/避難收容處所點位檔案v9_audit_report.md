# Audit Report: 避難收容處所點位檔案v9.csv

- Source file: `L:\2026_RS\data\避難收容處所點位檔案v9.csv`
- Audit time: 2026-03-03 15:32:13 +08:00
- Total records: 5973
- Backup file: `L:\2026_RS\data\避難收容處所點位檔案v9_backup_before_audit_20260303_153212.csv`
- Total corrections: 383

## Issue Summary

| Issue | Count |
|---|---:|
| Phone normalization | 348 |
| Leading/trailing whitespace | 24 |
| Invalid/unrecoverable phone content | 8 |
| Longitude out of Taiwan range (0) | 3 |

## Post-Fix Validation

- Remaining trim issues: 0
- Remaining longitude=0 (with Taiwan-latitude): 0
- Remaining phone scientific-notation values: 0

## Detailed Corrections (Every Issue)

| Line | Column | Issue | Before | After |
|---:|---|---|---|---|
| 33 | 管理人電話 | Phone normalization | 8712367＊710 | 8712367#710 |
| 60 | 管理人電話 | Phone normalization | 546365軍 | 546365 |
| 62 | 管理人電話 | Invalid/unrecoverable phone content | 4.72E+11 |  |
| 69 | 管理人電話 | Invalid/unrecoverable phone content | 4.72E+11 |  |
| 90 | 管理人電話 | Phone normalization | （089）731633 | (089)731633 |
| 94 | 管理人電話 | Phone normalization | （089）732073 | (089)732073 |
| 95 | 管理人電話 | Phone normalization | （089）731576 | (089)731576 |
| 97 | 管理人電話 | Phone normalization | （089）732017 | (089)732017 |
| 98 | 管理人電話 | Phone normalization | （089）732016#203 | (089)732016#203 |
| 215 | 管理人電話 | Phone normalization | 8714561＊130 | 8714561#130 |
| 219 | 管理人電話 | Phone normalization | 8711130＊31 | 8711130#31 |
| 233 | 管理人電話 | Phone normalization | 6426428轉940 | 6426428#940 |
| 246 | 管理人電話 | Phone normalization | 8014543＊110 | 8014543#110 |
| 250 | 管理人電話 | Phone normalization | 8215923＊311 | 8215923#311 |
| 252 | 管理人電話 | Phone normalization | 8010865＊31 | 8010865#31 |
| 255 | 管理人電話 | Phone normalization | 7879544轉32 | 7879544#32 |
| 257 | 管理人電話 | Phone normalization | 8062627＊301 | 8062627#301 |
| 258 | 管理人電話 | Phone normalization | 7875075轉30 | 7875075#30 |
| 260 | 管理人電話 | Phone normalization | 8036569＊731 | 8036569#731 |
| 262 | 管理人電話 | Phone normalization | 8215929＊100 | 8215929#100 |
| 275 | 管理人電話 | Phone normalization | 7911296＊31 | 7911296#31 |
| 279 | 管理人電話 | Phone normalization | 7910766＊310 | 7910766#310 |
| 285 | 管理人電話 | Phone normalization | 8215176轉179 | 8215176#179 |
| 288 | 管理人電話 | Phone normalization | 07-5712434轉31 | 07-5712434#31 |
| 289 | 管理人電話 | Phone normalization | 07-5714595轉31 | 07-5714595#31 |
| 299 | 管理人電話 | Phone normalization | 7881062轉40 | 7881062#40 |
| 306 | 管理人電話 | Phone normalization | 07-8151500分機107 | 07-8151500#107 |
| 323 | 管理人電話 | Phone normalization | 07-5712225轉731 | 07-5712225#731 |
| 332 | 管理人電話 | Phone normalization | 8215176轉179 | 8215176#179 |
| 334 | 管理人電話 | Phone normalization | 7812814轉40 | 7812814#40 |
| 335 | 管理人電話 | Phone normalization | 8215176轉179 | 8215176#179 |
| 336 | 管理人電話 | Phone normalization | 3368333轉2063 | 3368333#2063 |
| 337 | 管理人電話 | Phone normalization | 3368333轉2063 | 3368333#2063 |
| 338 | 管理人電話 | Phone normalization | 7828205轉40 | 7828205#40 |
| 343 | 管理人電話 | Phone normalization | 5715133轉731 | 5715133#731 |
| 345 | 管理人電話 | Phone normalization | 08-7792055轉14 | 08-7792055#14 |
| 350 | 管理人電話 | Phone normalization | 08-7792013轉14 | 08-7792013#14 |
| 369 | 管理人電話 | Phone normalization | 7812858轉40 | 7812858#40 |
| 378 | 管理人電話 | Phone normalization | 3368333轉2063 | 3368333#2063 |
| 384 | 管理人電話 | Phone normalization | 08-7793004轉13 | 08-7793004#13 |
| 392 | 管理人電話 | Phone normalization | 7811685轉40 | 7811685#40 |
| 419 | 管理人電話 | Phone normalization | 6516256轉30 | 6516256#30 |
| 422 | 管理人電話 | Phone normalization | 08-7783031轉14 | 08-7783031#14 |
| 431 | 管理人電話 | Phone normalization | 7032838轉40 | 7032838#40 |
| 435 | 管理人電話 | Phone normalization | 7033166轉310 | 7033166#310 |
| 441 | 管理人電話 | Phone normalization | 2862550#108、567 | 2862550#108/567 |
| 460 | 管理人電話 | Phone normalization | 3368333轉2063 | 3368333#2063 |
| 471 | 管理人電話 | Phone normalization | 08-7222812轉25 | 08-7222812#25 |
| 489 | 管理人電話 | Phone normalization | 07-6512541轉40 | 07-6512541#40 |
| 492 | 管理人電話 | Phone normalization | 3813210#5031、5311 | 3813210#5031/5311 |
| 494 | 管理人電話 | Phone normalization | 07-6512003轉135 | 07-6512003#135 |
| 495 | 管理人電話 | Phone normalization | 07-6512026轉311 | 07-6512026#311 |
| 498 | 管理人電話 | Phone normalization | 3368333轉2063 | 3368333#2063 |
| 519 | 管理人電話 | Phone normalization | 08-7701004轉10 | 08-7701004#10 |
| 521 | 管理人電話 | Phone normalization | 07-6515536轉13 | 07-6515536#13 |
| 532 | 管理人電話 | Phone normalization | 3368333轉2063 | 3368333#2063 |
| 536 | 管理人電話 | Phone normalization | （089）672506#11 | (089)672506#11 |
| 537 | 管理人電話 | Phone normalization | （089）672543#13 | (089)672543#13 |
| 545 | 管理人電話 | Phone normalization | （089）672548#12 | (089)672548#12 |
| 554 | 管理人電話 | Phone normalization | 08-7701864轉14 | 08-7701864#14 |
| 575 | 管理人電話 | Phone normalization | 08-7701200轉14 | 08-7701200#14 |
| 577 | 管理人電話 | Phone normalization | 07-6513752轉20 | 07-6513752#20 |
| 592 | 管理人電話 | Phone normalization | 3710981、3758030 | 3710981/3758030 |
| 596 | 管理人電話 | Phone normalization | 07-6512003轉135 | 07-6512003#135 |
| 605 | 管理人電話 | Phone normalization | 08-7991036轉14 | 08-7991036#14 |
| 606 | 管理人電話 | Phone normalization | 07-6561349轉30 | 07-6561349#30 |
| 626 | 管理人電話 | Phone normalization | 08-7991104分機308 | 08-7991104#308 |
| 644 | 管理人電話 | Phone normalization | 6172831轉31 | 6172831#31 |
| 650 | 管理人電話 | Phone normalization | 07-3513300轉113 | 07-3513300#113 |
| 654 | 管理人電話 | Phone normalization | 6101044（O）6178741（H） | 6101044/6178741 |
| 664 | 管理人電話 | Phone normalization | 07-6561527轉50 | 07-6561527#50 |
| 672 | 管理人電話 | Phone normalization | 6561921#1214，1217，1218 | 6561921#1214/1217/1218 |
| 673 | 管理人電話 | Phone normalization | 08-7902234轉123 | 08-7902234#123 |
| 680 | 管理人電話 | Phone normalization | 3368333轉2063 | 3368333#2063 |
| 683 | 管理人電話 | Phone normalization | 6110246轉123 | 6110246#123 |
| 687 | 管理人電話 | Phone normalization | 6176595（O）3893355（H） | 6176595/3893355 |
| 689 | 管理人電話 | Phone normalization | 07-6174111轉141或轉136 | 07-6174111#141/#136 |
| 694 | 經度 | Longitude out of Taiwan range (0) | 0 |  |
| 706 | 管理人電話 | Phone normalization | 3368333轉2063 | 3368333#2063 |
| 710 | 管理人電話 | Phone normalization | 6651182、0910848955 | 6651182/0910848955 |
| 716 | 管理人電話 | Phone normalization | 07-6191216轉22或轉50 | 07-6191216#22/#50 |
| 719 | 管理人電話 | Phone normalization | 6254220轉40 | 6254220#40 |
| 721 | 管理人電話 | Phone normalization | 6161411轉178 | 6161411#178 |
| 728 | 管理人電話 | Phone normalization | 6161411轉178 | 6161411#178 |
| 732 | 管理人電話 | Phone normalization | 3368333轉2063 | 3368333#2063 |
| 738 | 管理人電話 | Phone normalization | 07-6212815轉40 | 07-6212815#40 |
| 748 | 管理人電話 | Phone normalization | 3368333轉2063 | 3368333#2063 |
| 754 | 管理人電話 | Phone normalization | 07-6912716轉122 | 07-6912716#122 |
| 768 | 管理人電話 | Phone normalization | （089）571054 | (089)571054 |
| 778 | 管理人電話 | Phone normalization | 6663961、6663960、0975309223 | 6663961/6663960/0975309223 |
| 784 | 管理人電話 | Phone normalization | 6663279、0921208608 | 6663279/0921208608 |
| 785 | 管理人電話 | Phone normalization | 6613335、0932738714 | 6613335/0932738714 |
| 793 | 經度 | Longitude out of Taiwan range (0) | 0 |  |
| 797 | 管理人電話 | Phone normalization | 07-6361475轉41 | 07-6361475#41 |
| 803 | 管理人電話 | Phone normalization | （089）531224 | (089)531224 |
| 808 | 管理人電話 | Phone normalization | 07-6311177轉13或轉25 | 07-6311177#13/#25 |
| 810 | 管理人電話 | Phone normalization | 07-6812534＃40 | 07-6812534#40 |
| 811 | 經度 | Longitude out of Taiwan range (0) | 0 |  |
| 811 | 管理人電話 | Phone normalization | 6612502＃510 | 6612502#510 |
| 812 | 管理人電話 | Phone normalization | 6612715、0912710835 | 6612715/0912710835 |
| 820 | 管理人電話 | Phone normalization | 07-6616100轉122或轉128 | 07-6616100#122/#128 |
| 822 | 管理人電話 | Phone normalization | 07-6872100轉1133 | 07-6872100#1133 |
| 825 | 管理人電話 | Phone normalization | 06900001轉130/131 | 06900001#130/131 |
| 826 | 管理人電話 | Phone normalization | 6622059、0933375380 | 6622059/0933375380 |
| 831 | 管理人電話 | Phone normalization | 07-6814311轉15或轉14 | 07-6814311#15/#14 |
| 833 | 管理人電話 | Phone normalization | 07-6814311轉15或轉14 | 07-6814311#15/#14 |
| 840 | 管理人電話 | Phone normalization | 6618676、0910371752 | 6618676/0910371752 |
| 841 | 管理人電話 | Phone normalization | 07-6872366 、0958288315 | 07-6872366/0958288315 |
| 848 | 管理人電話 | Phone normalization | 6900001轉130/131 | 6900001#130/131 |
| 849 | 管理人電話 | Phone normalization | 06900001轉130/131 | 06900001#130/131 |
| 850 | 管理人電話 | Phone normalization | 089-551006分機252 | 089-551006#252 |
| 853 | 管理人電話 | Phone normalization | 6993008轉32 | 6993008#32 |
| 857 | 管理人電話 | Phone normalization | 6900001轉130/131 | 6900001#130/131 |
| 871 | 管理人電話 | Phone normalization | 3368333轉2063 | 3368333#2063 |
| 874 | 管理人電話 | Phone normalization | 089-541186村辦公處 | 089-541186 |
| 878 | 管理人電話 | Phone normalization | 06-2622458分機10 | 06-2622458#10 |
| 880 | 管理人電話 | Phone normalization | 06-2622460分機701 | 06-2622460#701 |
| 882 | 管理人電話 | Phone normalization | 6693457、0928707199 | 6693457/0928707199 |
| 899 | 管理人電話 | Phone normalization | 6691226、0937636150 | 6691226/0937636150 |
| 901 | 管理人電話 | Phone normalization | 06-2910126分機260 | 06-2910126#260 |
| 905 | 管理人電話 | Phone normalization | 089-892328宅089-891113村辦公處 | 089-892328/089-891113 |
| 943 | 管理人電話 | Phone normalization | 06-2633171分機100 | 06-2633171#100 |
| 945 | 管理人電話 | Phone normalization | 06-2157691分機217 | 06-2157691#217 |
| 948 | 管理人電話 | Phone normalization | 06-2630011分機200 | 06-2630011#200 |
| 953 | 管理人電話 | Phone normalization | 06-2617123分機502 | 06-2617123#502 |
| 1007 | 管理人電話 | Phone normalization | 089-891512宅089-891143村辦公處 | 089-891512/089-891143 |
| 1012 | 管理人電話 | Phone normalization | 089-891011泰源國小 | 089-891011 |
| 1047 | 管理人電話 | Phone normalization | 6893923、0926393713 | 6893923/0926393713 |
| 1099 | 管理人電話 | Phone normalization | 089-891588宅089-891173村辦公處 | 089-891588/089-891173 |
| 1102 | 管理人電話 | Phone normalization | 6791413、0963114332 | 6791413/0963114332 |
| 1120 | 管理人電話 | Phone normalization | 089-891103公 | 089-891103 |
| 1136 | 管理人電話 | Phone normalization | 675299810、675299831 | 675299810/675299831 |
| 1188 | 管理人電話 | Phone normalization | 675101810、 675101840 | 675101810/675101840 |
| 1190 | 管理人電話 | Phone normalization | 6751025111、6751025140 | 6751025111/6751025140 |
| 1275 | 管理人電話 | Phone normalization | 089-850862胡文清 | 089-850862 |
| 1312 | 管理人電話 | Phone normalization | 6761065100、6761065400 | 6761065100/6761065400 |
| 1522 | 管理人電話 | Phone normalization | 05-2521310轉28 | 05-2521310#28 |
| 1525 | 管理人電話 | Phone normalization | 05-2521310轉29 | 05-2521310#29 |
| 1527 | 管理人電話 | Phone normalization | 05-2521310轉36 | 05-2521310#36 |
| 1550 | 管理人電話 | Phone normalization | 05-2521310轉28 | 05-2521310#28 |
| 1585 | 管理人電話 | Phone normalization | 05-2521310轉28 | 05-2521310#28 |
| 1724 | 管理人電話 | Phone normalization | 05-2591322 05-2593352 | 05-259132205-2593352 |
| 1819 | 管理人電話 | Phone normalization | 05-2110534＃13 | 05-2110534#13 |
| 1820 | 管理人電話 | Phone normalization | 05-2110534＃13 | 05-2110534#13 |
| 1821 | 管理人電話 | Phone normalization | 05-2611472＃101 | 05-2611472#101 |
| 1824 | 管理人電話 | Phone normalization | 2612843＃13 | 2612843#13 |
| 1825 | 管理人電話 | Phone normalization | 2612843＃13 | 2612843#13 |
| 1834 | 管理人電話 | Phone normalization | 05-2541005＃50 | 05-2541005#50 |
| 1835 | 管理人電話 | Phone normalization | 05-2541005＃50 | 05-2541005#50 |
| 1853 | 管理人電話 | Phone normalization | 05-2790508＃101 | 05-2790508#101 |
| 1854 | 管理人電話 | Phone normalization | 05-2790508＃101 | 05-2790508#101 |
| 1911 | 管理人電話 | Phone normalization | 05-2611018＃10 | 05-2611018#10 |
| 1916 | 管理人電話 | Phone normalization | 05-2541041＃12 | 05-2541041#12 |
| 1917 | 管理人電話 | Phone normalization | 05-2541041＃12 | 05-2541041#12 |
| 1930 | 避難收容處所地址 | Leading/trailing whitespace | 松中村蔦松路213號　 | 松中村蔦松路213號 |
| 1932 | 村里 | Leading/trailing whitespace | 　埔村 | 埔村 |
| 1932 | 避難收容處所地址 | Leading/trailing whitespace | 瓊埔村瓊埔路48號　 | 瓊埔村瓊埔路48號 |
| 1950 | 避難收容處所地址 | Leading/trailing whitespace | 松北村蔦松路1-1號　 | 松北村蔦松路1-1號 |
| 1975 | 避難收容處所地址 | Leading/trailing whitespace | 山腳村蕃東路1號　 | 山腳村蕃東路1號 |
| 2040 | 避難收容處所地址 | Leading/trailing whitespace | 大溝村大溝路1號　 | 大溝村大溝路1號 |
| 2056 | 避難收容處所地址 | Leading/trailing whitespace | 水北村水林路12號　 | 水北村水林路12號 |
| 2081 | 避難收容處所名稱 | Leading/trailing whitespace | 樹腳社區活動中心　 | 樹腳社區活動中心 |
| 2094 | 管理人電話 | Phone normalization | 06-9921731轉122 | 06-9921731#122 |
| 2398 | 管理人電話 | Phone normalization | 03-8762771轉191 | 03-8762771#191 |
| 2675 | 管理人電話 | Phone normalization | 04-8761122轉259 | 04-8761122#259 |
| 2837 | 管理人電話 | Phone normalization | 2974133分機13 | 2974133#13 |
| 3048 | 管理人電話 | Phone normalization | 03-8358100轉838413 | 03-8358100#838413 |
| 3115 | 管理人電話 | Phone normalization | 04-8520149＃111 | 04-8520149#111 |
| 3217 | 管理人電話 | Phone normalization | 7682323總幹事 | 7682323 |
| 3309 | 管理人電話 | Phone normalization | 04-22713625732溫山明0923152541 | 04-22713625732/0923152541 |
| 3357 | 管理人電話 | Phone normalization | 04-22702664630溫彥程0937-218039 | 04-22702664630/0937-218039 |
| 3372 | 管理人電話 | Phone normalization | 04-22703129185許伯進0911-767912 | 04-22703129185/0911-767912 |
| 3383 | 管理人電話 | Phone normalization | 04-23712324轉730 | 04-23712324#730 |
| 3386 | 管理人電話 | Phone normalization | 04-22245200分機704 | 04-22245200#704 |
| 3404 | 管理人電話 | Phone normalization | 04-23755959分機731 | 04-23755959#731 |
| 3415 | 管理人電話 | Phone normalization | 04-22701567#730彭怡文 | 04-22701567#730 |
| 3416 | 管理人電話 | Phone normalization | 04-23722866分機730 | 04-23722866#730 |
| 3420 | 管理人電話 | Phone normalization | 04-22245200分機508 | 04-22245200#508 |
| 3423 | 管理人電話 | Phone normalization | 22289111分機33920 | 22289111#33920 |
| 3456 | 管理人電話 | Phone normalization | 04-23956005804陳永澤 | 04-23956005804 |
| 3457 | 管理人電話 | Phone normalization | 04-23212041分機721 | 04-23212041#721 |
| 3458 | 管理人電話 | Phone normalization | 04-22245200分機202 | 04-22245200#202 |
| 3463 | 管理人電話 | Phone normalization | 04-2271593372朱信德 | 04-2271593372 |
| 3467 | 管理人電話 | Phone normalization | 0423172860分機730 | 0423172860#730 |
| 3468 | 管理人電話 | Phone normalization | 0423224690分機731 | 0423224690#731 |
| 3493 | 管理人電話 | Phone normalization | 04-22314031轉156 | 04-22314031#156 |
| 3519 | 管理人電話 | Phone normalization | 04-22391647轉8310.8301 | 04-22391647#8310/8301 |
| 3585 | 管理人電話 | Phone normalization | 04-25651300 #832 | 04-25651300#832 |
| 3620 | 管理人電話 | Phone normalization | 04-25811574分機41 | 04-25811574#41 |
| 3674 | 管理人電話 | Phone normalization | 04-26578270#520.521 | 04-26578270#520/521 |
| 3677 | 管理人電話 | Phone normalization | 04-25283556#241、243 | 04-25283556#241/243 |
| 3696 | 預計收容村里 | Leading/trailing whitespace | 泰昌　 | 泰昌 |
| 3719 | 管理人電話 | Phone normalization | 04-25873442分機205 | 04-25873442#205 |
| 3817 | 管理人電話 | Invalid/unrecoverable phone content | 陳政治 |  |
| 3853 | 管理人電話 | Phone normalization | 082-322581‧325705 | 082-322581/325705 |
| 3868 | 管理人電話 | Phone normalization | 037-991111分機107 | 037-991111#107 |
| 3937 | 預計收容村里 | Leading/trailing whitespace | 玉泉村　館中村　館東村　 | 玉泉村　館中村　館東村 |
| 4000 | 管理人電話 | Phone normalization | 037—921451#03 | 037-921451#03 |
| 4001 | 管理人電話 | Phone normalization | 037—921451#13 | 037-921451#13 |
| 4032 | 管理人電話 | Phone normalization | 037—722547#241 | 037-722547#241 |
| 4033 | 管理人電話 | Phone normalization | 037—722547#241 | 037-722547#241 |
| 4048 | 管理人電話 | Phone normalization | 037—723853#10 | 037-723853#10 |
| 4052 | 管理人電話 | Phone normalization | 037-543250轉136 | 037-543250#136 |
| 4053 | 管理人電話 | Phone normalization | 037-543250轉136 | 037-543250#136 |
| 4074 | 管理人電話 | Phone normalization | 037-562773轉145 | 037-562773#145 |
| 4075 | 管理人電話 | Phone normalization | 037-562773轉145 | 037-562773#145 |
| 4084 | 管理人電話 | Phone normalization | 037—432784#14 | 037-432784#14 |
| 4085 | 管理人電話 | Phone normalization | 037—432784#14 | 037-432784#14 |
| 4105 | 管理人電話 | Phone normalization | 03-5949052＃100 | 03-5949052#100 |
| 4110 | 管理人電話 | Phone normalization | 037—431235#12 | 037-431235#12 |
| 4111 | 管理人電話 | Phone normalization | 037—431235#13 | 037-431235#13 |
| 4121 | 管理人電話 | Phone normalization | 03-9506763張文哲 | 03-9506763 |
| 4150 | 管理人電話 | Phone normalization | 03-9545102轉253 | 03-9545102#253 |
| 4167 | 管理人電話 | Phone normalization | 037-462101轉110 | 037-462101#110 |
| 4254 | 管理人電話 | Phone normalization | 03-9255600轉402 | 03-9255600#402 |
| 4266 | 管理人電話 | Phone normalization | 03-5966177＃206 | 03-5966177#206 |
| 4267 | 管理人電話 | Phone normalization | 03-9253794轉103 | 03-9253794#103 |
| 4277 | 管理人電話 | Phone normalization | 03-5966177＃550 | 03-5966177#550 |
| 4285 | 管理人電話 | Phone normalization | O：5373184-130 | 5373184-130 |
| 4289 | 管理人電話 | Phone normalization | 9231991分機401 | 9231991#401 |
| 4300 | 管理人電話 | Phone normalization | 03-9322942分機5033 | 03-9322942#5033 |
| 4305 | 管理人電話 | Phone normalization | 03-9324153轉100 | 03-9324153#100 |
| 4307 | 管理人電話 | Phone normalization | 03-9383792分機104或114 | 03-9383792#104/114 |
| 4309 | 管理人電話 | Phone normalization | 03-9322210轉511 | 03-9322210#511 |
| 4311 | 管理人電話 | Phone normalization | 03-9323795轉1104 | 03-9323795#1104 |
| 4313 | 管理人電話 | Phone normalization | 03-9322077轉1833 | 03-9322077#1833 |
| 4314 | 管理人電話 | Phone normalization | 03-9384147轉510 | 03-9384147#510 |
| 4315 | 管理人電話 | Phone normalization | O：5373543-12 | 5373543-12 |
| 4329 | 管理人電話 | Phone normalization | 03-9322309轉282 | 03-9322309#282 |
| 4332 | 管理人電話 | Phone normalization | O：5374793-609 | 5374793-609 |
| 4349 | 管理人電話 | Phone normalization | 03-9283791轉410 | 03-9283791#410 |
| 4362 | 管理人電話 | Phone normalization | 04-25812116分機611 | 04-25812116#611 |
| 4369 | 管理人電話 | Phone normalization | O：5775645 | 5775645 |
| 4386 | 管理人電話 | Phone normalization | O：5238075-130 | 5238075-130 |
| 4390 | 管理人電話 | Phone normalization | O：5736666-302 | 5736666-302 |
| 4394 | 管理人電話 | Phone normalization | O：5386204-33 | 5386204-33 |
| 4404 | 管理人電話 | Phone normalization | 5222492分機2040 | 5222492#2040 |
| 4410 | 管理人電話 | Phone normalization | O：5222109-8602 | 5222109-8602 |
| 4419 | 管理人電話 | Phone normalization | O：5328283 | 5328283 |
| 4421 | 管理人電話 | Phone normalization | O：5711125-107 | 5711125-107 |
| 4423 | 管理人電話 | Phone normalization | O：5326345-16 | 5326345-16 |
| 4427 | 管理人電話 | Phone normalization | O：5316668-205 | 5316668-205 |
| 4429 | 管理人電話 | Phone normalization | 5152525轉300 | 5152525#300 |
| 4432 | 管理人電話 | Phone normalization | O：5316605-132 | 5316605-132 |
| 4488 | 管理人電話 | Phone normalization | 02-26720067分機13 | 02-26720067#13 |
| 4509 | 管理人電話 | Phone normalization | 02-26711017分機207 | 02-26711017#207 |
| 4510 | 管理人電話 | Phone normalization | 02-26616482＃50 | 02-26616482#50 |
| 4553 | 管理人電話 | Phone normalization | 2661-6421轉302 | 2661-6421#302 |
| 4585 | 管理人電話 | Phone normalization | 03-4782024分機513 | 03-4782024#513 |
| 4592 | 管理人電話 | Phone normalization | 02-26712523分機150 | 02-26712523#150 |
| 4593 | 管理人電話 | Phone normalization | 02-26723302分機240 | 02-26723302#240 |
| 4596 | 管理人電話 | Phone normalization | 02-26711017分機207 | 02-26711017#207 |
| 4601 | 管理人電話 | Phone normalization | 02-2673-1201分機501 | 02-2673-1201#501 |
| 4609 | 管理人電話 | Phone normalization | 02-26711895分機830 | 02-26711895#830 |
| 4631 | 管理人電話 | Phone normalization | 02-26726521分機115 | 02-26726521#115 |
| 4635 | 管理人電話 | Phone normalization | 02-26726783分機102 | 02-26726783#102 |
| 4636 | 管理人電話 | Phone normalization | 02-26717851分機150 | 02-26717851#150 |
| 4640 | 管理人電話 | Phone normalization | 02-86712590分機831 | 02-86712590#831 |
| 4645 | 管理人電話 | Phone normalization | 02-26712392分機41 | 02-26712392#41 |
| 4647 | 管理人電話 | Phone normalization | 02-26731488分機221 | 02-26731488#221 |
| 4661 | 管理人電話 | Phone normalization | 02-86764945分機12 | 02-86764945#12 |
| 4665 | 管理人電話 | Phone normalization | 02-26711018分機832 | 02-26711018#832 |
| 4666 | 管理人電話 | Phone normalization | 26711017分機207 | 26711017#207 |
| 4699 | 管理人電話 | Phone normalization | 26745666分機830 | 26745666#830 |
| 4735 | 管理人電話 | Phone normalization | 26742666分機600 | 26742666#600 |
| 4772 | 管理人電話 | Phone normalization | 26801958轉205 | 26801958#205 |
| 4876 | 避難收容處所名稱 | Leading/trailing whitespace | 北新國小　 | 北新國小 |
| 4887 | 管理人電話 | Phone normalization | 26806673轉831 | 26806673#831 |
| 4920 | 管理人電話 | Phone normalization | 86865486轉842 | 86865486#842 |
| 4925 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 4926 | 管理人電話 | Phone normalization | 02-22659858 02-22736647 | 02-2265985802-22736647 |
| 4947 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 4968 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 4971 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 4979 | 管理人電話 | Phone normalization | 26812014轉832 | 26812014#832 |
| 4987 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 4995 | 管理人電話 | Phone normalization | 29350955＃715 | 29350955#715 |
| 4997 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 5009 | 管理人電話 | Phone normalization | 2570-2330轉6423 | 2570-2330#6423 |
| 5013 | 管理人電話 | Phone normalization | 26812625轉841 | 26812625#841 |
| 5019 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 5021 | 管理人電話 | Invalid/unrecoverable phone content | 2.66E+15 |  |
| 5023 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 5030 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 5033 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 5040 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 5045 | 管理人電話 | Phone normalization | 26812475轉831 | 26812475#831 |
| 5052 | 管理人電話 | Phone normalization | 02-22482688＃286 | 02-22482688#286 |
| 5062 | 管理人電話 | Phone normalization | 86625802-86625802-86625800夜 | 86625802-86625802-86625800 |
| 5067 | 管理人電話 | Invalid/unrecoverable phone content | 2.66E+15 |  |
| 5090 | 管理人電話 | Invalid/unrecoverable phone content | 2.66E+15 |  |
| 5096 | 管理人電話 | Phone normalization | 2231-9670轉232 | 2231-9670#232 |
| 5099 | 管理人電話 | Phone normalization | 2570-2330轉6424 | 2570-2330#6424 |
| 5105 | 管理人電話 | Phone normalization | 8926-4470轉800 | 8926-4470#800 |
| 5165 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5170 | 管理人電話 | Phone normalization | 2570-2330轉6429 | 2570-2330#6429 |
| 5179 | 管理人電話 | Invalid/unrecoverable phone content | 2.97E+11 |  |
| 5185 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5206 | 管理人電話 | Phone normalization | 02-24931111轉124 | 02-24931111#124 |
| 5221 | 管理人電話 | Phone normalization | 23033555轉600 | 23033555#600 |
| 5233 | 管理人電話 | Phone normalization | 27255200分機2247 | 27255200#2247 |
| 5243 | 管理人電話 | Phone normalization | 2570-2330轉6429 | 2570-2330#6429 |
| 5245 | 管理人電話 | Phone normalization | 02-277181211分機1336 | 02-277181211#1336 |
| 5273 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5296 | 管理人電話 | Phone normalization | 02-26711017分機207 | 02-26711017#207 |
| 5322 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5331 | 管理人電話 | Phone normalization | 03-3520000ext.173 | 03-3520000#173 |
| 5338 | 管理人電話 | Phone normalization | 02-27618156~611 | 02-27618156/611 |
| 5340 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5359 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5364 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5365 | 管理人電話 | Phone normalization | 03-3520000ext.172 | 03-3520000#172 |
| 5368 | 管理人電話 | Phone normalization | 02-24901480、02-24901845 | 02-24901480/02-24901845 |
| 5378 | 管理人電話 | Phone normalization | 03-3520000ext.173 | 03-3520000#173 |
| 5387 | 預計收容村里 | Leading/trailing whitespace | 成功里、福祉里、福民里、重明里、光明里、光正里、同安里、同慶里、菜寮里、永春里、中正里、吉利里、福德里　　 | 成功里、福祉里、福民里、重明里、光明里、光正里、同安里、同慶里、菜寮里、永春里、中正里、吉利里、福德里 |
| 5393 | 管理人電話 | Phone normalization | 02-24901418、02-24902616 | 02-24901418/02-24902616 |
| 5404 | 管理人電話 | Phone normalization | 27255200分機5517 | 27255200#5517 |
| 5407 | 預計收容村里 | Leading/trailing whitespace | 成功里、福祉里、福民里、過田里、重明里、光田里、光陽里、光明里、光正里、菜寮里、中正里、福德里、同安里、永春里　 | 成功里、福祉里、福民里、過田里、重明里、光田里、光陽里、光明里、光正里、菜寮里、中正里、福德里、同安里、永春里 |
| 5414 | 預計收容村里 | Leading/trailing whitespace | 菜寮里、永春里、中正里、吉利里、大同里、中民里、平和里、大安里、忠孝里、仁義里、光輝里、福利里、仁德里　 | 菜寮里、永春里、中正里、吉利里、大同里、中民里、平和里、大安里、忠孝里、仁義里、光輝里、福利里、仁德里 |
| 5417 | 預計收容村里 | Leading/trailing whitespace | 同慶里、大同里、中民里、平和里、大安里、仁德里、忠孝里、仁義里、光榮里、光輝里、福星里、福利里、清和里、永興里、文化里、錦通里、光華里、大德里　　 | 同慶里、大同里、中民里、平和里、大安里、仁德里、忠孝里、仁義里、光榮里、光輝里、福星里、福利里、清和里、永興里、文化里、錦通里、光華里、大德里 |
| 5422 | 管理人電話 | Phone normalization | 26416170分機13 | 26416170#13 |
| 5424 | 預計收容村里 | Leading/trailing whitespace | 光陽里、重明里、光田里、福祉里、過田里、錦田里、光明里、中山里　 | 光陽里、重明里、光田里、福祉里、過田里、錦田里、光明里、中山里 |
| 5430 | 預計收容村里 | Leading/trailing whitespace | 過田里、錦田里、光田里、重陽里　 | 過田里、錦田里、光田里、重陽里 |
| 5439 | 管理人電話 | Phone normalization | 2570-2330轉6427 | 2570-2330#6427 |
| 5447 | 管理人電話 | Phone normalization | 02-24931111轉124 | 02-24931111#124 |
| 5452 | 預計收容村里 | Leading/trailing whitespace | 錦田里、三民里、中山里、大園里、國隆里、重陽里、民生里、重新里、正德里、正義里、幸福里　　 | 錦田里、三民里、中山里、大園里、國隆里、重陽里、民生里、重新里、正德里、正義里、幸福里 |
| 5462 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5463 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5474 | 管理人電話 | Phone normalization | 02-29862345轉493 | 02-29862345#493 |
| 5508 | 預計收容村里 | Leading/trailing whitespace | 厚德里、維德里、尚德里、永德里、立德里　 | 厚德里、維德里、尚德里、永德里、立德里 |
| 5514 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5520 | 管理人電話 | Phone normalization | 26343888＃130 | 26343888#130 |
| 5524 | 預計收容村里 | Leading/trailing whitespace | 厚德里、維德里、永德里、永煇里　 | 厚德里、維德里、永德里、永煇里 |
| 5533 | 預計收容村里 | Leading/trailing whitespace | 永盛里、永福里、永清里、永安里、溪美里、福隆里、慈福里、慈生里、慈惠里、慈愛里、永吉里、永順里、永豐里、福樂里、仁華里　 | 永盛里、永福里、永清里、永安里、溪美里、福隆里、慈福里、慈生里、慈惠里、慈愛里、永吉里、永順里、永豐里、福樂里、仁華里 |
| 5537 | 預計收容村里 | Leading/trailing whitespace | 永盛里、永福里、永清里、永安里、福隆里、慈福里、慈生里、慈愛里、永吉里、永順里、永豐里、福樂里、仁華里　 | 永盛里、永福里、永清里、永安里、福隆里、慈福里、慈生里、慈愛里、永吉里、永順里、永豐里、福樂里、仁華里 |
| 5597 | 預計收容村里 | Leading/trailing whitespace | 富貴里、富福里、碧華里　 | 富貴里、富福里、碧華里 |
| 5601 | 預計收容村里 | Leading/trailing whitespace | 五常里、五福里、仁忠里、慈化里、慈祐里、五華里、富貴里、富福里、碧華里、五順里、富華里　 | 五常里、五福里、仁忠里、慈化里、慈祐里、五華里、富貴里、富福里、碧華里、五順里、富華里 |
| 5602 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5609 | 管理人電話 | Phone normalization | 2570-2330轉6428 | 2570-2330#6428 |
| 5621 | 管理人電話 | Phone normalization | 02-22916051分#113 | 02-22916051/#113 |
| 5646 | 管理人電話 | Phone normalization | 03-3520000ext.176 | 03-3520000#176 |
| 5647 | 管理人電話 | Phone normalization | 28311004轉231 | 28311004#231 |
| 5655 | 管理人電話 | Phone normalization | 02-24903410、02-24991601#255 | 02-24903410/02-24991601#255 |
| 5665 | 管理人電話 | Phone normalization | 02-24515601轉30 | 02-24515601#30 |
| 5678 | 管理人電話 | Phone normalization | 02-24565663轉80 | 02-24565663#80 |
| 5687 | 管理人電話 | Phone normalization | 02-24903410、02-24941601#255 | 02-24903410/02-24941601#255 |
| 5701 | 管理人電話 | Phone normalization | 24301122 ext.307 | 24301122#307 |
| 5714 | 管理人電話 | Phone normalization | 24301122 ext.319 | 24301122#319 |
| 5717 | 管理人電話 | Phone normalization | 24301122 ext.308 | 24301122#308 |
| 5719 | 管理人電話 | Phone normalization | 24301122 ext.205 | 24301122#205 |
| 5720 | 管理人電話 | Phone normalization | 24301122 ext.315 | 24301122#315 |
| 5721 | 管理人電話 | Phone normalization | 24301122 ext.308 | 24301122#308 |
| 5722 | 管理人電話 | Phone normalization | 02-24301122 ext.313 | 02-24301122#313 |
| 5727 | 管理人電話 | Phone normalization | 24301122 ext.319 | 24301122#319 |
| 5730 | 管理人電話 | Phone normalization | 24301122 ext.316 | 24301122#316 |
| 5737 | 管理人電話 | Phone normalization | 24301122 ext.312 | 24301122#312 |
| 5738 | 管理人電話 | Phone normalization | 02-24301122 ext.312 | 02-24301122#312 |
| 5739 | 管理人電話 | Phone normalization | 24301122 ext.308 | 24301122#308 |
| 5740 | 管理人電話 | Phone normalization | 24301122 ext.308 | 24301122#308 |
| 5742 | 管理人電話 | Phone normalization | 24301122 ext.312 | 24301122#312 |
| 5744 | 管理人電話 | Phone normalization | 24301122 ext.309 | 24301122#309 |
| 5746 | 管理人電話 | Phone normalization | 24301122 ext.316 | 24301122#316 |
| 5747 | 管理人電話 | Phone normalization | 24301122ext.311.308 | 24301122#311/308 |
| 5748 | 管理人電話 | Phone normalization | 24301122 ext.310 | 24301122#310 |
| 5753 | 管理人電話 | Phone normalization | 24301122 ext.316 | 24301122#316 |
| 5755 | 管理人電話 | Phone normalization | 24301122 ext.307 | 24301122#307 |
| 5757 | 管理人電話 | Phone normalization | 02-24275518 ext.22 | 02-24275518#22 |
| 5762 | 管理人電話 | Phone normalization | 24301122 ext.307 | 24301122#307 |
| 5764 | 管理人電話 | Phone normalization | （02）24220814#30、31 | (02)24220814#30/31 |
| 5766 | 管理人電話 | Phone normalization | 24301122 ext.309 | 24301122#309 |
| 5774 | 管理人電話 | Phone normalization | 02-24652133 ext.30 | 02-24652133#30 |
| 5800 | 管理人電話 | Phone normalization | 23116117分機604380 | 23116117#604380 |
| 5803 | 管理人電話 | Phone normalization | 2570-2330轉6428 | 2570-2330#6428 |
| 5825 | 管理人電話 | Phone normalization | 02-24696000 ext.1014 | 02-24696000#1014 |
| 5842 | 管理人電話 | Invalid/unrecoverable phone content | 2.61E+11 |  |
| 5906 | 管理人電話 | Phone normalization | 24985966轉173 | 24985966#173 |
| 5909 | 管理人電話 | Phone normalization | 02-24985965轉188 | 02-24985965#188 |
| 5916 | 管理人電話 | Phone normalization | 02-24985966轉188 | 02-24985966#188 |
| 5918 | 管理人電話 | Phone normalization | 02-24985966轉188 | 02-24985966#188 |
| 5923 | 管理人電話 | Phone normalization | 02-24985965轉188 | 02-24985965#188 |
| 5924 | 管理人電話 | Phone normalization | 02-24985966轉188 | 02-24985966#188 |
| 5941 | 管理人電話 | Phone normalization | 02-2638-1273轉134 | 02-2638-1273#134 |
| 5943 | 管理人電話 | Phone normalization | 2638-1273轉134 | 2638-1273#134 |
