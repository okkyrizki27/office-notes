/****** Object:  View [dbo].[vw_monitoring_mapping_equipment]    Script Date: 2026-06-17 14:54:30 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

-- =======================================================================================================================================
-- Author:      Ivan Tri Wibowo
-- Create Date: 2023-04-12
-- Description: Mapping Table Equipment
-- Modified by : 20240316 ivan - Add source table equipment from dbplan
--				 20241121 ivan - Add section COAL TRANSPORT
--				 20250609 ivan - remark section GRADER dan DOZER karena dijadikan 1 section SGE
--				 20251020 ivan - remark WHEN UPPER(b.sectiontypename) = 'OB LOADER' THEN 'BIG DIGGER'
-- =======================================================================================================================================
CREATE   VIEW [dbo].[vw_monitoring_mapping_equipment]
AS

	WITH cte_digital AS (
		SELECT TOP 1 WITH TIES
			a.siteid as [site_id],
			CONVERT(varchar(13), UPPER(a.equipmentname)) as equipment,
			CASE
				--WHEN UPPER(b.sectiontypename) = 'OB LOADER' THEN 'BIG DIGGER'
				--WHEN modelunit = 'GD825A-2' THEN 'GRADER'
				--WHEN modelunit IN ('D375A-5','D375A-6R','D10T2','D155A-6','D8T') THEN 'DOZER'
				WHEN UPPER(b.sectiontypename) = 'SUPPORT GEAR EQUIPMENT' THEN 'SGE'
				WHEN modelunit IN ('R620','FH16','SST115','SST150','SST110','SST125') THEN 'COAL TRANSPORT'
				ELSE UPPER(b.sectiontypename)
			END as section,
			a.modelunit as model_unit
		FROM [dbo].[equipment] a
		LEFT JOIN (
			SELECT DISTINCT
				sectiontypecode,
				sectiontypename
			FROM [dbo].[sectiontype]
		) b on a.sectiontypecode = b.sectiontypecode
		WHERE a.isactive = 1
		ORDER BY ROW_NUMBER() OVER(PARTITION BY siteid, equipmentname ORDER BY a.modifiedutcdate DESC)
	)

	SELECT
		site_id,
		equipment,
		CONVERT(varchar(25), section) section,
		CONVERT(varchar(55), model_unit) model_unit,
		CONVERT(varchar(25), section) equipment_group
	FROM cte_digital
	--WHERE section IN ('OB HAULER', 'BIG DIGGER', 'DOZER', 'GRADER', 'COAL TRANSPORT')
	WHERE section IN ('OB HAULER', 'OB LOADER', 'SGE', 'COAL TRANSPORT')

GO
