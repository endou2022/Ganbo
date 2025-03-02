SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

DROP SCHEMA IF EXISTS ganbo;
CREATE DATABASE IF NOT EXISTS `ganbo` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `ganbo`;

CREATE TABLE `automatic` (
  `ID` int(11) UNSIGNED NOT NULL,
  `キーワード` varchar(256) NOT NULL,
  `タイプ` varchar(20) NOT NULL DEFAULT 'NO',
  `サービスID` int(11) UNSIGNED NOT NULL DEFAULT 0,
  `ジャンル番号` int(11) NOT NULL DEFAULT 99,
  `録画マージン前` int(11) NOT NULL DEFAULT 25,
  `録画マージン後` int(11) NOT NULL DEFAULT 30,
  `登録日時` timestamp NOT NULL DEFAULT current_timestamp(),
  `更新日時` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `channels` (
  `タイプ` varchar(10) NOT NULL,
  `チャンネル` varchar(255) NOT NULL,
  `ID` bigint(20) UNSIGNED NOT NULL,
  `サービスID` int(11) UNSIGNED NOT NULL,
  `ネットワークID` int(10) UNSIGNED NOT NULL,
  `サービス名` varchar(255) NOT NULL,
  `有効` varchar(20) NOT NULL DEFAULT 'checked',
  `表示順` int(10) UNSIGNED NOT NULL DEFAULT 10
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `genres` (
  `ジャンル番号` int(11) NOT NULL,
  `ジャンル` varchar(255) NOT NULL,
  `ジャンルクラス` varchar(255) NOT NULL,
  `色` varchar(20) NOT NULL DEFAULT '#ffffff' COMMENT '興味のあるジャンルのみ色をつける'
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `genres` (`ジャンル番号`, `ジャンル`, `ジャンルクラス`, `色`) VALUES
(0, 'ニュース／報道', 'genre0', '#ffffff'),
(1, 'スポーツ', 'genre1', '#ffffff'),
(2, '情報／ワイドショー', 'genre2', '#ffffff'),
(3, 'ドラマ', 'genre3', '#ffd2bd'),
(4, '音楽', 'genre4', '#ffffff'),
(5, 'バラエティ', 'genre5', '#ffffff'),
(6, '映画', 'genre6', '#a2ffd0'),
(7, 'アニメ／特撮', 'genre7', '#ceceff'),
(8, 'ドキュメンタリー／教養', 'genre8', '#ffffff'),
(9, '劇場／公演', 'genre9', '#ffffff'),
(10, '趣味／教育', 'genre10', '#ffffff'),
(11, '福祉', 'genre11', '#ffffff'),
(12, '(予備)', 'genre12', '#ffffff'),
(13, '(予備)', 'genre13', '#ffffff'),
(14, '拡張', 'genre14', '#ffffff'),
(15, 'その他', 'genre15', '#ffffff'),
(16, '予約(有効)', 'valid_reserved', '#e763d2'),
(17, '予約(無効)', 'invalid_reserved', '#c6c6c6');

CREATE TABLE `programs` (
  `ID` bigint(20) UNSIGNED NOT NULL,
  `イベントID` int(11) UNSIGNED NOT NULL,
  `サービスID` int(11) UNSIGNED NOT NULL,
  `ネットワークID` int(11) UNSIGNED NOT NULL,
  `開始時刻` datetime NOT NULL,
  `放送時間` int(11) UNSIGNED NOT NULL COMMENT '単位はsec',
  `終了時刻` datetime NOT NULL,
  `フリー` varchar(10) NOT NULL DEFAULT 'true',
  `番組名` varchar(255) NOT NULL DEFAULT '-' COMMENT '検索対象',
  `説明` varchar(500) NOT NULL DEFAULT '-',
  `ジャンル番号` int(11) NOT NULL DEFAULT 15,
  `拡張情報` varchar(1000) NOT NULL DEFAULT '-',
  `予約` enum('○','×') DEFAULT NULL COMMENT 'NULL:予約なし\r\n○:予約\r\n×:予約無効',
  `自動予約ID` int(11) DEFAULT NULL COMMENT '番号がある場合、自動予約',
  `録画マージン前` int(11) NOT NULL DEFAULT 25 COMMENT '単位はsec',
  `録画マージン後` int(11) NOT NULL DEFAULT -30 COMMENT '単位はsec',
  `保存ファイル名` varchar(255) DEFAULT NULL COMMENT '変更は詳細ダイアローグから行う',
  `録画状況` varchar(200) NOT NULL DEFAULT '未録画' COMMENT '録画タスクの状況'
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `setting` (
  `ID` int(11) NOT NULL,
  `キー` varchar(255) NOT NULL,
  `値` varchar(255) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `setting` (`ID`, `キー`, `値`) VALUES
(1, 'IPアドレス', '192.168.11.75'),
(2, 'ポート番号', '40772'),
(3, '録画マージン前', '25'),
(4, '録画マージン後', '30'),
(5, '番組情報更新時刻', '04:30'),
(6, '保存ファイル名マクロ', '($ServiceName$)$Title$.ts'),
(7, '保存ルート', '/mnt/ts');


ALTER TABLE `automatic`
  ADD PRIMARY KEY (`ID`);

ALTER TABLE `channels`
  ADD PRIMARY KEY (`ID`);

ALTER TABLE `genres`
  ADD PRIMARY KEY (`ジャンル番号`);

ALTER TABLE `programs`
  ADD PRIMARY KEY (`ID`);

ALTER TABLE `setting`
  ADD PRIMARY KEY (`ID`);


ALTER TABLE `automatic`
  MODIFY `ID` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `setting`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
