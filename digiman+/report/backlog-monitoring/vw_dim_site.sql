CREATE   view [bigdata_mart].[vw_dim_site]
as
	select
		site_id COLLATE SQL_Latin1_General_CP1_CI_AS AS site_id,
		site_code COLLATE SQL_Latin1_General_CP1_CI_AS AS site_code,
		site_name COLLATE SQL_Latin1_General_CP1_CI_AS AS site_name,
		[created_date],
		[modified_date]
	from (
		select 
			convert(varchar(4), [site_id]) [site_id], 
			case 
				WHEN [site_id]='2001' then 'LAT'
				WHEN [site_id]='2002' THEN 'BIN'
				WHEN [site_id]='2003' THEN 'ADR'
				WHEN [site_id]='2004' THEN 'KDC'
				WHEN [site_id]='2005' THEN 'SDJ'
				WHEN [site_id]='2006' THEN 'TAM'
				WHEN [site_id]='2007' THEN 'PAD'
				WHEN [site_id]='2008' THEN 'IBP'
				WHEN [site_id]='2009' THEN 'IPR'
				WHEN [site_id]='2010' THEN 'ADT'
				WHEN [site_id]='2011' THEN 'PKP'
				WHEN [site_id]='2090' THEN 'BRC'
				WHEN [site_id]='D000' THEN 'DOID'
				WHEN [site_id]='3001' THEN 'ADR CP'
				WHEN [site_id]='3002' THEN 'AMC HAJU'
				WHEN [site_id]='3003' THEN 'AMC CHPP'
				WHEN [site_id]='2000' THEN 'HO'
				WHEN [site_id]='3000' THEN 'INFRA'
				WHEN [site_id]='2101' THEN 'BSF'
				WHEN [site_id]='2102' THEN 'RO'
				WHEN [site_id]='3004' THEN 'IM'
				WHEN [site_id]='3005' THEN 'INM'
				ELSE ''
			end [site_code], 
			[site_name], 
			[created_date], 
			[modified_date]
		from 
			[app_opex].[dbo].[vw_mcc_sap_mssite]
		where [isdeleted] = 0

		UNION ALL

		SELECT * FROM (
			select '2101' site_id, 'BSF' site_code, 'BUMA-Support Facility' site_name, GETDATE() created_date, GETDATE() modified_date UNION ALL
			select '2102' site_id, 'RO' site_code, 'BUMA-Rep Office Tanjung Redeb' site_name, GETDATE() created_date, GETDATE() modified_date UNION ALL
			select '3000' site_id, 'INFRA' site_code, 'BUMA-Infra-Head Office' site_name, GETDATE() created_date, GETDATE() modified_date UNION ALL
			select '3001' site_id, 'ADR CP' site_code, 'BUMA-ADARO Wara Crushing Plant' site_name, GETDATE() created_date, GETDATE() modified_date UNION ALL
			select '3002' site_id, 'AMC HAJU' site_code, 'BUMA-AMC Haju Road' site_name, GETDATE() created_date, GETDATE() modified_date UNION ALL
			select '3003' site_id, 'AMC CHPP' site_code, 'BUMA-AMC CHPP' site_name, GETDATE() created_date, GETDATE() modified_date UNION ALL
			select '3004' site_id, 'IM' site_code, 'BUMA-Infra-Mining Related' site_name, GETDATE() created_date, GETDATE() modified_date UNION ALL
			select '3005' site_id, 'INM' site_code, 'BUMA-Infra-Non Mining Related' site_name, GETDATE() created_date, GETDATE() modified_date
		) a
	) as [source]
GO


