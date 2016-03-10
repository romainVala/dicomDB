
-- --------------------------------------------------------
--
-- Stand-in structure for view `ExamSerie`
--
DROP VIEW IF EXISTS `ExamSeries`;

 CREATE VIEW ExamSeries AS Select e.*, s.*  from exam e, serie s where e.Eid = s.ExamRef;


CREATE VIEW ExamSeries AS Select  e.ExamName, e.ExamNum, e.PatientsName, e/AcquisitionTime, s.*, e.dicom_dir from exam e, serie s where e.Eid = s.ExamRef

-- --------------------------------------------------------

--
-- Structure for view `seqname`
--
DROP TABLE IF EXISTS `seqname`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `seqname` AS select `serie`.`Sid` AS `Sid`,`serie`.`ExamRef` AS `ExamRef`,`serie`.`SName` AS `SName`,`serie`.`SNumber` AS `SNumber`,`serie`.`dimX` AS `dimX`,`serie`.`dimY` AS `dimY`,`serie`.`dimZ` AS `dimZ`,`serie`.`dim4` AS `dim4`,`serie`.`sizeX` AS `sizeX`,`serie`.`sizeY` AS `sizeY`,`serie`.`sizeZ` AS `sizeZ`,`serie`.`SliceGap` AS `SliceGap`,`serie`.`dimPhase` AS `dimPhase`,`serie`.`TR` AS `TR`,`serie`.`TE` AS `TE`,`serie`.`TI` AS `TI`,`serie`.`FA` AS `FA`,`serie`.`PixelBw` AS `PixelBw`,`serie`.`PhaseAngle` AS `PhaseAngle`,`serie`.`PhaseDir` AS `PhaseDir`,`serie`.`PatMode` AS `PatMode`,`serie`.`Affine` AS `Affine`,`serie`.`CoilName` AS `CoilName`,`serie`.`AcqTime` AS `AcqTime`,`serie`.`Duration` AS `Duration`,`serie`.`SeqName` AS `SeqName`,`serie`.`SeqName2` AS `SeqName2`,`serie`.`ImageType` AS `ImageType`,`serie`.`SliceTime` AS `SliceTime`,`serie`.`TablePos` AS `TablePos`,`serie`.`nb_dic_file` AS `nb_dic_file` from `serie` group by `serie`.`SeqName2`;

