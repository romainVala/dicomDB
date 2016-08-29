-- phpMyAdmin SQL Dump
-- version 3.4.11.1deb2
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Nov 25, 2013 at 10:03 AM
-- Server version: 5.5.31
-- PHP Version: 5.4.4-14+deb7u5

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `cenir`
--

-- --------------------------------------------------------

--
-- Table structure for table `exam`
--

DROP TABLE IF EXISTS `serie`;
DROP TABLE IF EXISTS `exam`;


CREATE TABLE IF NOT EXISTS `exam` (
  `Eid` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ExamName` varchar(50) NOT NULL DEFAULT '',
  `ExamNum` int(11) DEFAULT NULL,
  `MachineName` varchar(15) DEFAULT NULL,
  `PatientsName` varchar(100) DEFAULT NULL,
  `AcquisitionTime` timestamp NULL DEFAULT NULL,
  `StudyTime` timestamp NULL DEFAULT NULL,
  `ExamDuration` int(4) DEFAULT NULL,
  `PatientsBirthDate` date DEFAULT NULL,
  `PatientsSex` char(1) NOT NULL DEFAULT 'O',
  `PatientsWeight` float DEFAULT NULL,
  `SoftwareVersions` varchar(50) DEFAULT NULL,
  `PatientsAge` int(4) DEFAULT NULL,
  `FirstSerieName` text,
  `LastSerieName`  text,
  `dicom_dir` text,
  `EUID` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`Eid`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 ;

-- --------------------------------------------------------
--
-- Table structure for table `serie`
--
CREATE TABLE IF NOT EXISTS `serie` (
  `Sid` int(11) NOT NULL AUTO_INCREMENT,
  `ExamRef` int(11) unsigned NOT NULL,
  `SName` text CHARACTER SET latin1 COLLATE latin1_bin NOT NULL,
  `SNumber` int(11) NOT NULL,
  `dimX` int(11) DEFAULT NULL,
  `dimY` int(11) DEFAULT NULL,
  `dimZ` int(11) DEFAULT NULL,
  `dim4` int(11) DEFAULT NULL,
  `sizeX` float DEFAULT NULL,
  `sizeY` float DEFAULT NULL,
  `sizeZ` float DEFAULT NULL,
  `SliceGap` float DEFAULT NULL,
  `dimPhase` int(11) DEFAULT NULL,
  `TR` float DEFAULT NULL,
  `TE` float DEFAULT NULL,
  `TEvec` text,
  `TI` int(8) DEFAULT NULL,
  `FA` float DEFAULT NULL,
  `PhaseAngle` float DEFAULT NULL,
  `PhaseDir` varchar(5) DEFAULT NULL,
  `PatMode` text,
  `Concat` int(8) DEFAULT NULL,
  `CGating` int(8) DEFAULT NULL,
  `Orient` text,
  `Affine` text,
  `DiffBval` int(8) DEFAULT NULL,
  `DiffNbDir` int(8) DEFAULT NULL,
  `CoilName` varchar(20) DEFAULT NULL,
  `AcqTime` timestamp NULL DEFAULT NULL,
  `Duration` int(8) DEFAULT NULL,
  `Duration2` int(11) DEFAULT NULL,
  `SeqName` varchar(50) CHARACTER SET latin1 COLLATE latin1_bin DEFAULT NULL,
  `SeqName2` varchar(500) CHARACTER SET latin1 COLLATE latin1_bin DEFAULT NULL,
  `SeqType` varchar(15) DEFAULT NULL,
  `ImageType` text CHARACTER SET latin1 COLLATE latin1_bin,
  `SliceTime` text,
  `slicemode` int(4) DEFAULT NULL,
  `PixelBw` int(4) DEFAULT NULL,
  `PhaseBw` float DEFAULT NULL,
  `TablePos` int(11) DEFAULT NULL,
  `nb_dic_file` int(11) DEFAULT NULL,
  `fsize` bigint(20) DEFAULT NULL,
  `corrupt` text,
  `dicom_sdir` text,
  `nifti_dir` text,
  `nifti_volumes` text,
  `SUID` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`Sid`),
  FOREIGN KEY (`ExamRef`) REFERENCES exam(`Eid`) ON DELETE CASCADE
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 ;

-- --------------------------------------------------------
--
-- Table structure for table `results_anat`
--
DROP TABLE IF EXISTS `results_anat`;

CREATE TABLE IF NOT EXISTS `results_anat` (
 `Rid` int(11) unsigned NOT NULL AUTO_INCREMENT,
 `Sid` int(11)  NOT NULL,
 `status` tinyint(1)  NOT NULL,
 `vbmgrayvol` float DEFAULT NULL,
 `vbmwhitevol` float DEFAULT NULL,
 `vbmcsfvol` float DEFAULT NULL,
 `dir_path` text DEFAULT NULL,	
  PRIMARY KEY (`Rid`),
  FOREIGN KEY (`Sid`) REFERENCES serie(`Sid`) ON DELETE CASCADE
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 ;

-- --------------------------------------------------------
--
-- Table structure for table `quality_serie`
--
DROP TABLE IF EXISTS `quality_serie`;

CREATE TABLE IF NOT EXISTS `quality_serie` (
 `Qid` int(11) unsigned NOT NULL AUTO_INCREMENT,
 `Sid` int(11)  NOT NULL,
 `content` text DEFAULT NULL,	
 `reviewby` text DEFAULT NULL,	
 `subj_artefact` text DEFAULT NULL,
 `phys_artefact` text DEFAULT NULL, 
  PRIMARY KEY (`Qid`),
  FOREIGN KEY (`Sid`) REFERENCES serie(`Sid`) ON DELETE NO ACTION
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 ;


/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
