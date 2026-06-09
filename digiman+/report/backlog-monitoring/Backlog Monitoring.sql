/****** Object:  StoredProcedure [dbo].[usp_iams_backlog_monitoring]    Script Date: 2026-05-22 10:26:18 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


-- =============================================
-- author:      varian aditya iryanto
-- create date: 2026-04-21
-- description: sp for creating backlog monitoring and dump it to file
-- =============================================
CREATE procedure [dbo].[usp_iams_backlog_monitoring]
(
	@yearmonth varchar(6)
)
as
begin
    -- set nocount on added to prevent extra result sets from
    -- interfering with select statements.
    set nocount on

--=========================================================IAMS Digiman-DExecute Source========================================================

	-- MOBacklog
	drop table if exists #mobacklog
	create table #mobacklog 
	(
		[monumber] varchar(12),
	    [siteid] varchar(4),
	    [moyear] int,
	    [momonthly] int,
		[equipmentid] varchar(20),
		[motype] varchar(12),
		[unitmodel] varchar(50),
		[unitsection] varchar(150),
		[modescription] varchar(max),
		[mocreateddate] date,
		[mocreatedby] varchar(100),
		[moupdateddate] date,
		[moupdatedby] varchar(100),
		[motecodate] date,
		[replacementstatuslvl1] varchar(100),
	    [plancost] numeric(18,10), 
	    [actualcost] numeric(18,10), 
	    [userstatus] varchar(50),
	    [systemstatus] varchar(150),
	)
	
	begin try
		declare @query_mobacklog  nvarchar(4000)
		set @query_mobacklog = 
		'select substring(monumber, 3, len(monumber)-1) monumber, siteid, moyear, momonthly, equipmentid, motype, unitmodel, unitsection, modescription, mocreateddate, mocreatedby, moupdateddate,
		moupdatedby, motecodate, replacementstatuslvl1, plancost, actualcost, userstatus, systemstatus
		from openrowset 
		(
			bulk ''assetmanagement/buma/digiman_dexecute/mobacklog/'',
			data_source = ''curated_dfs_core_windows_net'',
			format = ''delta''
		) a
		where mocreatedby = ''DATACOM'' and replacementstatuslvl1 = ''BEX'' and motype = ''MT01''
		and month_id = '+ @yearmonth + '
		'
		--and siteid in (''2001'', ''2002'', ''2009'') 
		insert into #mobacklog exec(@query_mobacklog)
	end try
	begin catch
		 -- do nothing
	end catch

--==================================================================================================================================================
--=========================================================IAMS Digiman-DOrder Source========================================================
	
	-- Lookup
	drop table if exists #lookup
	create table #lookup 
	(
		[lookupcode] varchar(32),
		[lookupname] varchar(128),
	)

	declare @query_lookup nvarchar(4000)
	set @query_lookup =
	'select lookupcode, lookupname from openrowset 
	(
		bulk ''assetmanagement/buma/digiman_dorder/lookup/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where  isactive = 1 and lookupcategory = ''MOL_LAST_STATUS''
	'
	insert into #lookup exec(@query_lookup)  -----------GA ADA DI MKP

--==================================================================================================================================================
--=========================================================IAMS Digiman-DPlan Source================================================================

	-- Digital Planning
	drop table if exists #digitalplanning
	create table #digitalplanning 
	(
	    [planid] bigint
	)

	declare @query_digitalplanning nvarchar(4000)
	set @query_digitalplanning =
	'select planid from openrowset 
	(
		bulk ''assetmanagement/buma/digiman_dplan/digitalplanning/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where status in (''SUBMIT'', ''INPROGRESS'') and month_id = '+ @yearmonth + '
	'
	insert into #digitalplanning exec(@query_digitalplanning)


	-- DP Column
	drop table if exists #dpcolumn
	create table #dpcolumn 
	(
	    [columnid] bigint,
	    [planid] bigint
	)

	declare @query_dpcolumn nvarchar(4000)
	set @query_dpcolumn = 
	'select columnid, planid from openrowset 
	(
		bulk ''assetmanagement/buma/digiman_dplan/dpcolumn/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where lower(name) = ''mo number'' and month_id = '+ @yearmonth + '
	'
	insert into #dpcolumn exec(@query_dpcolumn)


	-- DP Value
	drop table if exists #dpvalue
	create table #dpvalue 
	(
	    [columnid] bigint,
	    [value] varchar(1000)
	)

	declare @query_dpvalue nvarchar(4000)
	set @query_dpvalue = 
	'select columnid, [value] from openrowset 
	(
		bulk ''assetmanagement/buma/digiman_dplan/dpvalue/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where month_id = '+ @yearmonth + '
	'
	insert into #dpvalue exec(@query_dpvalue)

--==================================================================================================================================================
--=========================================================IAMS Maintencane-Execution Source========================================================

	-- Work Order
	drop table if exists #workorder
	create table #workorder 
	(
	    [id] int,
		[number] varchar(16),
	    [maintenancecategorycode] varchar(200)
	)

	declare @query_workorder nvarchar(4000)
	set @query_workorder = 
	'select id, number, maintenancecategorycode from openrowset 
	(
		bulk ''assetmanagement/buma/iams_maintenance_execution/workorder/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1  and month_id = '+ @yearmonth + '
	'
	--and typecode = ''Inspection''
	insert into #workorder exec(@query_workorder)


	-- Task
	drop table if exists #task
	create table #task 
	(
	    [id] int,
		[workorderid] int
	)

	declare @query_task nvarchar(4000)
	set @query_task = 
	'select id, workorderid from openrowset 
	(
		bulk ''assetmanagement/buma/iams_maintenance_execution/task/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1 and month_id = '+ @yearmonth + '
	'
	--and type = ''FlexiInspection''
	insert into #task exec(@query_task)


	-- Task Personalized
	drop table if exists #taskpersonalized
	create table #taskpersonalized 
	(
	    [id] int,
		[taskid] int
	)

	declare @query_taskpersonalized nvarchar(4000)
	set @query_taskpersonalized = 
	'select id, taskid from openrowset 
	(
		bulk ''assetmanagement/buma/iams_maintenance_execution/taskpersonalized/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1 and month_id = '+ @yearmonth + '
	'
	insert into #taskpersonalized exec(@query_taskpersonalized)


	-- Task Personalized Finding
	drop table if exists #taskpersonalizedfinding
	create table #taskpersonalizedfinding 
	(
	    [id] int,
		[taskpersonalizedid] int,
		[componentcode] varchar(64),
		[subcomponentcode] varchar(64),
		[actionremedycode] varchar(64),
		[prioritycode] varchar(64)
	)

	declare @query_taskpersonalizedfinding nvarchar(4000)
	set @query_taskpersonalizedfinding = 
	'select id, taskpersonalizedid, componentcode, subcomponentcode, actionremedycode, prioritycode from openrowset 
	(
		bulk ''assetmanagement/buma/iams_maintenance_execution/taskpersonalizedfinding/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1 and month_id = '+ @yearmonth + '
	'
	insert into #taskpersonalizedfinding exec(@query_taskpersonalizedfinding)

--==================================================================================================================================================
--=========================================================IAMS Maintencane-Order Source============================================================

	-- Check Part Order
	drop table if exists #checkpartorder
	create table #checkpartorder 
	(
	    [monumber] varchar(50),
	    [grstatus] varchar(64),
	    [gistatus] varchar(64)
	)

	declare @query_checkpartorder nvarchar(4000)
	set @query_checkpartorder = 
	'select monumber, grstatus, gistatus from openrowset 
	(
		bulk ''assetmanagement/buma/iams_maintenance_order/checkpartorder/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1 and month_id = '+ @yearmonth + '
	'
	insert into #checkpartorder exec(@query_checkpartorder)


	-- Mechanic Order Detail
	drop table if exists #mechanicorderdetail
	create table #mechanicorderdetail 
	(
	    [id] int,
		[mechanicorderlistid] int,
		[componentcode] varchar(64),
		[subcomponentcode] varchar(64),
		[actionremedycode] varchar(64),
		[prioritycode] varchar(64),
	)

	declare @query_mechanicorderdetail nvarchar(4000)
	set @query_mechanicorderdetail = 
	'select id, mechanicorderlistid, componentcode, subcomponentcode, actionremedycode, prioritycode from openrowset 
	(
		bulk ''assetmanagement/buma/iams_maintenance_order/mechanicorderdetail/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1 and month_id = '+ @yearmonth + '
	'
	insert into #mechanicorderdetail exec(@query_mechanicorderdetail)


	-- Mechanic Order List
	drop table if exists #mechanicorderlist
	create table #mechanicorderlist 
	(
	    [id] int,
		[workorderid] int,
		[taskpersonalizedfindingid] int,
		[mechanicordersummaryid] int,
		[number] varchar(200),
		[edd] datetime,
		[status] varchar(200),
		[isactive] bit,
		[createdby] varchar(128),
		[createdat] datetime
	)

	declare @query_mechanicorderlist nvarchar(4000)
	set @query_mechanicorderlist = 
	'select id, workorderid, taskpersonalizedfindingid, mechanicordersummaryid, number, edd, [status], 
	isactive, createdby, createdat from openrowset 
	(
		bulk ''assetmanagement/buma/iams_maintenance_order/mechanicorderlist/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where month_id = '+ @yearmonth + '
	'
	insert into #mechanicorderlist exec(@query_mechanicorderlist)


	-- Mechanic Order Material
	drop table if exists #mechanicordermaterial
	create table #mechanicordermaterial 
	(
	    [id] bigint,
	    [mechanicorderlistid] bigint,
		[materialnumber] varchar(200)
	)

	declare @query_mechanicordermaterial nvarchar(4000)
	set @query_mechanicordermaterial = 
	'select id, mechanicorderlistid, materialnumber from openrowset 
	(
		bulk ''assetmanagement/buma/iams_maintenance_order/mechanicordermaterial/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1 and month_id = '+ @yearmonth + '
	'
	insert into #mechanicordermaterial exec(@query_mechanicordermaterial)

	
	-- Mechanic Order Summary
	drop table if exists #mechanicordersummary
	create table #mechanicordersummary 
	(
	    [id] int,
		[maintenancecategorycode] varchar(64),
		[number] varchar(200)
	)

	declare @query_mechanicordersummary nvarchar(4000)
	set @query_mechanicordersummary = 
	'select id, maintenancecategorycode, number from openrowset 
	(
		bulk ''assetmanagement/buma/iams_maintenance_order/mechanicordersummary/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1 and month_id = '+ @yearmonth + '
	'
	insert into #mechanicordersummary exec(@query_mechanicordersummary)


	-- Pooling MO Item
	drop table if exists #poolingmoitem
	create table #poolingmoitem 
	(
	    [poolingid] bigint,
	    [modetailmaterialid] bigint,
		[materialnumber] varchar(50),
		[emolnumber] varchar(50)
	)

	declare @query_poolingmoitem nvarchar(4000)
	set @query_poolingmoitem = 
	'select poolingid, modetailmaterialid, materialnumber, emolnumber from openrowset 
	(
		bulk ''assetmanagement/buma/iams_maintenance_order/poolingmoitem/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1 and month_id = '+ @yearmonth + '
	'
	insert into #poolingmoitem exec(@query_poolingmoitem)


	-- SAP MO Sync Order
	drop table if exists #sapmosyncorder
	create table #sapmosyncorder 
	(
	    [poolingid] int,
	    [mono] varchar(32)
	)

	declare @query_sapmosyncorder nvarchar(4000)
	set @query_sapmosyncorder = 
	'select poolingid, mono from openrowset 
	(
		bulk ''assetmanagement/buma/iams_maintenance_order/sapmosyncorder/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where month_id = '+ @yearmonth + '
	'
	insert into #sapmosyncorder exec(@query_sapmosyncorder)


--==================================================================================================================================================
--=========================================================IAMS Services Asset Source===============================================================

	-- Action Remedy
	drop table if exists #actionremedy
	create table #actionremedy 
	(
	    [code] varchar(64),
		[name] varchar(200)
	)

	declare @query_actionremedy nvarchar(4000)
	set @query_actionremedy = 
	'select code, [name] from openrowset 
	(
		bulk ''assetmanagement/buma/iams_services_asset/actionremedy/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1
	'
	insert into #actionremedy exec(@query_actionremedy)


	-- Asset
	drop table if exists #asset
	create table #asset 
	(
	    [assetnumber] varchar(200),
		[assetmodelcode] varchar(64),
		[sectiontypecode] varchar(64)
	)

	declare @query_asset nvarchar(4000)
	set @query_asset = 
	'select assetnumber, assetmodelcode, sectiontypecode from openrowset 
	(
		bulk ''assetmanagement/buma/iams_services_asset/asset/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1
	'
	insert into #asset exec(@query_asset)


	-- Asset Model
	drop table if exists #assetmodel
	create table #assetmodel 
	(
	    [code] varchar(64),
		[name] varchar(200)
	)

	declare @query_assetmodel nvarchar(4000)
	set @query_assetmodel = 
	'select code, [name] from openrowset 
	(
		bulk ''assetmanagement/buma/iams_services_asset/assetmodel/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1
	'
	insert into #assetmodel exec(@query_assetmodel)

	
	-- Component
	drop table if exists #component
	create table #component 
	(
	    [code] varchar(64),
		[name] varchar(200),
	)

	declare @query_component nvarchar(4000)
	set @query_component = 
	'select code, [name] from openrowset 
	(
		bulk ''assetmanagement/buma/iams_services_asset/component/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1
	'
	insert into #component exec(@query_component)


	-- Priority
	drop table if exists #priority
	create table #priority 
	(
	    [code] varchar(64),
		[name] varchar(200),
		[description] varchar(max)
	)

	declare @query_priority nvarchar(4000)
	set @query_priority = 
	'select code, [name], [description] from openrowset 
	(
		bulk ''assetmanagement/buma/iams_services_asset/priority/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1 and [group] = ''Inspection''
	'
	insert into #priority exec(@query_priority)


	-- Sub Component
	drop table if exists #subcomponent
	create table #subcomponent 
	(
	    [code] varchar(64),
		[name] varchar(200)
	)

	declare @query_subcomponent nvarchar(4000)
	set @query_subcomponent = 
	'select code, [name] from openrowset 
	(
		bulk ''assetmanagement/buma/iams_services_asset/subcomponent/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1
	'
	insert into #subcomponent exec(@query_subcomponent)

--==================================================================================================================================================
--=========================================================IAMS Workflow Source=====================================================================

	-- Workflow Transaction
	drop table if exists #workflowtransaction
	create table #workflowtransaction 
	(
	    [referencetransactionid] bigint,
	    [status] varchar(32),
	    [createdat] datetime,
	    [modifiedby] varchar(200)
	)

	declare @query_workflowtransaction nvarchar(4000)
	set @query_workflowtransaction = 
	'select referencetransactionid, [status], createdat, modifiedby from openrowset 
	(
		bulk ''assetmanagement/buma/iams_workflow/workflowtransaction/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1
	'
	insert into #workflowtransaction exec(@query_workflowtransaction)

--==================================================================================================================================================
--=========================================================Shared Tenant Source=====================================================================
	
	-- Section Type
	drop table if exists #sectiontype
	create table #sectiontype 
	(
	    [code] varchar(64),
		[name] varchar(200),
	)

	declare @query_sectiontype nvarchar(4000)
	set @query_sectiontype = 
	'select code, [name] from openrowset 
	(
		bulk ''assetmanagement/buma/shared_tenant/sectiontype/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1 and tenantcode = ''BUMAID''
	'
	insert into #sectiontype exec(@query_sectiontype)


	-- Site
	drop table if exists #site
	create table #site 
	(
	    [code] varchar(64),
		[name] varchar(100),
		[utcoffset] int
	)

	declare @query_site nvarchar(4000)
	set @query_site = 
	'select code, name, utcoffset from openrowset 
	(
		bulk ''assetmanagement/buma/shared_tenant/site/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1 and tenantcode = ''BUMAID''
	'
	insert into #site exec(@query_site)

--==================================================================================================================================================
--=========================================================Shared User Source=======================================================================

	-- User
	drop table if exists #user
	create table #user 
	(
	    [code] varchar(128),
		[fullname] varchar(max),
	)

	
	declare @query_user nvarchar(4000)
	set @query_user = 
	'select code, fullname from openrowset 
	(
		bulk ''assetmanagement/buma/shared_user/user/'',
		data_source = ''curated_dfs_core_windows_net'',
		format = ''delta''
	) a
	where isactive = 1
	'
	insert into #user exec(@query_user)

--===================================================================================================================================================
--=========================================================DIM Data Source=======================================================================

	-- Dim Equipment
	drop table if exists #dim_equipment
	create table #dim_equipment 
	(
	    [equipment] varchar(50),
	    [model_unit] varchar(50),
		[section_type_code_name] varchar(512),
	    [status_unit] varchar(10)
	)

	
	declare @query_dim_equipment nvarchar(4000)
	set @query_dim_equipment = 
	'select equipment, model_unit, section_type_code_name, status_unit from openrowset 
	(
		bulk ''assetmanagement/buma/reports/digiman/dim_equipment_mobacklog/*.parquet'',
		data_source = ''datamart_dfs_core_windows_net'',
		format = ''parquet''
	) a
	'
	insert into #dim_equipment exec(@query_dim_equipment) -----------GA ADA DI MKP


	-- Dim Date
	drop table if exists #dim_date
	create table #dim_date 
	(
	    [date_id] date,
	    [week_id] int
	)

	-- Dim Date
	declare @query_dim_date nvarchar(4000)
	set @query_dim_date =
	'select date_id, week_id from openrowset 
	(
		bulk ''assetmanagement/buma/reports/digiman/dim_date/*.parquet'',
		data_source = ''datamart_dfs_core_windows_net'',
		format = ''parquet''
	) a
	'
	insert into #dim_date exec(@query_dim_date) -----------GA ADA DI MKP

--===================================================================================================================================================
--=========================================================Mapping Data Source=======================================================================

	-- Mapping MOL Status
	drop table if exists #mapping_mol_status
	create table #mapping_mol_status 
	(
	    [status] varchar(10),
		[mol_status] varchar(30),
		[is_active] bit,
		[workflow_transaction_status] varchar(30),
		[require_mono] bit
	)

	declare @query_mapping_mol_status nvarchar(4000)
	set @query_mapping_mol_status =
	'select status, mol_status, is_active, workflow_transaction_status, require_mono from openrowset 
	(
		bulk ''assetmanagement/buma/mapping/config_mapping_mol_status.csv'',
		data_source = ''config_dfs_core_windows_net'',
		format = ''csv'',
		parser_version = ''2.0'',
		firstrow = 2
	) 
	with
	(
		[status] varchar(10),
		[mol_status] varchar(30),
		[is_active] bit,
		[workflow_transaction_status] varchar(30),
		[require_mono] bit
	) as result
	'
	insert into #mapping_mol_status exec(@query_mapping_mol_status)

--==================================================================================================================================================
--=========================================================CTE Transformation Process===============================================================
	
	;with maintenance_execution_transformation as
	(
		select
			wo.id as workorderid 
			,tpf.id as taskpersonalizedfindingid
			,tpf.taskpersonalizedid as taskpersonalizedid
			,wo.number as mono
			,wo.maintenancecategorycode as inspectiontype
			,tpf.componentcode as componentcode
			,tpf.subcomponentcode as subcomponentcode
			,tpf.actionremedycode as actionremedycode
			,tpf.prioritycode as prioritycode
		from #workorder wo
		inner join #task t 
		on wo.id = t.workorderid
		left join #taskpersonalized as tp
		on t.id = tp.taskid
		left join #taskpersonalizedfinding as tpf
		on tp.id = tpf.taskpersonalizedid
	),
	maintenance_order_transformation as
	(
		select * from
		(
			select 
				case when mos.id is null then 0 else 1 end summaryreference
				,sso.mono as mo_number
				,mol.workorderid 
				,mol.taskpersonalizedfindingid
				,mod.id as mechanicorderdetailid
				,mol.createdat as submit_emol_date
				,mos.number as mono
				,mos.maintenancecategorycode as inspectiontype
				,mod.componentcode as componentcode
				,mod.subcomponentcode as subcomponentcode
				,mod.actionremedycode as actionremedycode
				,mod.prioritycode as prioritycode
				,mol.number as emolno
				,mol.edd as eddmol
				,u1.fullname as emol_created_by
				,mmls.[status] as emol_status
				,case when coalesce(wft1.[status], wft2.[status]) = 'Complete' then u2.fullname end as approved_by
				,case when coalesce(wft1.[status], wft2.[status]) = 'Complete' then coalesce(wft1.createdat, wft2.createdat) end as approval_date
				,
				case 
					when mmls.require_mono is not null  then
						case 
							when 
								mol.isactive = mmls.is_active and isnull(coalesce(wft1.[status], wft2.[status]), '') = isnull(mmls.workflow_transaction_status, '')
								and case when sso.mono is null then 0 else 1 end = mmls.require_mono 
							then 1 
							else 0 
						end
					else 
						case 
							when mol.isactive = mmls.is_active and isnull(coalesce(wft1.[status], wft2.[status]), '') = isnull(mmls.workflow_transaction_status, '') then 1
							else 0
						end
				end correct_status 
			from #mechanicorderlist mol
			left join #mechanicordersummary mos
			on mol.mechanicordersummaryid = mos.id
			left join #mechanicorderdetail mod 
			on mol.id = mod.mechanicorderlistid
			left join #mechanicordermaterial mom
			on mol.id = mom.mechanicorderlistid
			left join #poolingmoitem pmi1 
			on mol.number = pmi1.emolnumber and mom.mechanicorderlistid is null
			left join #poolingmoitem pmi2
			on mol.number = pmi2.emolnumber and mom.materialnumber = pmi2.materialnumber
			left join #sapmosyncorder sso
			on sso.poolingid = coalesce(pmi1.poolingid, pmi2.poolingid)
			left join #workflowtransaction wft1
			on mol.workorderid = wft1.referencetransactionid
			left join #workflowtransaction wft2
			on mol.mechanicordersummaryid = wft2.referencetransactionid 
			left join #user u1
			on mol.createdby = u1.code
			left join #user u2
			on coalesce(wft1.[status], wft2.[status]) = 'Complete' and coalesce(wft1.modifiedby, wft2.modifiedby) = u2.code 
			left join 
			(	
				select mms.*, l.lookupname as status_desc from #mapping_mol_status mms
				left join #lookup l
				on mms.[status] = l.lookupcode
			) mmls
			on mol.[status] = mmls.mol_status
		) a
		where correct_status = 1
	),
	base_dplan as
	(
		select distinct 
			dpv.value 
		from #digitalplanning dp
		inner join #dpcolumn dpc
		on dp.planid = dpc.planid
		inner join #dpvalue dpv
		on dpc.columnid = dpv.columnid
	),
	base_order as
	(
		select 
			a.summaryreference
			,a.mo_number
			,a.workorderid
			,a.taskpersonalizedfindingid
			,a.mechanicorderdetailid
			,a.submit_emol_date
			,a.mono as mo_inspection_number
			,a.inspectiontype as inspection_type
			,c.[name] as component
			,sc.[name] as sub_component
			,ar.[name] as [action]
			,p.[name] as [priority]
			,a.emolno as emol_number
			,a.eddmol as edd
			,a.emol_created_by
			,a.emol_status
			,a.approved_by
			,a.approval_date
		
		from 
		(
			select distinct
				mot.summaryreference
				,mot.mo_number
				,mot.workorderid
				,mot.taskpersonalizedfindingid
				,mot.mechanicorderdetailid
				,mot.submit_emol_date
				,coalesce(mot.mono, met.mono) as mono
				,coalesce(mot.inspectiontype, met.inspectiontype) as inspectiontype
				,coalesce(mot.componentcode, met.componentcode) as componentcode
				,coalesce(mot.subcomponentcode, met.subcomponentcode) as subcomponentcode
				,coalesce(mot.actionremedycode, met.actionremedycode) as actionremedycode
				,coalesce(mot.prioritycode, met.prioritycode) as prioritycode
				,mot.emolno
				,mot.eddmol
				,mot.emol_created_by
				,mot.emol_status
				,mot.approved_by
				,mot.approval_date
			from maintenance_order_transformation mot
			left join maintenance_execution_transformation met 
			on met.workorderid = mot.workorderid and met.taskpersonalizedfindingid = mot.taskpersonalizedfindingid and mot.summaryreference = 0
		) a
		left join #component c
		on a.componentcode = c.code
		left join #subcomponent sc
		on a.subcomponentcode = sc.code
		left join #actionremedy ar
		on a.actionremedycode = ar.code
		left join #priority p 
		on a.prioritycode = p.code
	),
	base_backlog as
	(
		select distinct 
			mob.siteid as site_id
			,s.[name] as site_area
			,s.utcoffset
			,st.[name] as section
			,am.[name] as equipment_model 
			,mob.equipmentid as equipment_number
			,mob.motype as mo_type
			,mob.monumber as mo_number 
			,
			case 
				when isnull(mob.plancost, 0) = 0 then 'No Material'
				else 'Material'
			end as mo_category
			,mob.mocreateddate as created_on
			,mob.moyear as [year]
			,mob.momonthly as [month]
			,dd.week_id as [week]
			,mob.plancost as total_planned_costs
			,mob.actualcost as total_actual_costs
			,mob.userstatus as user_status
			,mob.systemstatus as system_status
			,mob.replacementstatuslvl1 as maintenance_activity_type
			,mob.mocreatedby as created_by
			,mob.motecodate as mo_teco_date
			,mob.moupdatedby as updated_by
			,
			case 
				when mob.motecodate is null then datediff(day, mob.mocreateddate, dateadd(hour, s.utcoffset, getutcdate()))
				else datediff(day, mob.mocreateddate, mob.motecodate)
			end aging_days
			,de.status_unit status_equipment
			,case when mob.motecodate is not null then 'Closed' else 'Open' end status_follow_up
		from #mobacklog mob
		left join #site s
		on mob.siteid = s.code
		inner join #dim_equipment de
		on lower(mob.equipmentid) = lower(de.equipment) 
		left join #asset a
		on de.equipment = a.assetnumber
		left join #assetmodel am
		on a.assetmodelcode = am.code
		left join #sectiontype st
		on a.sectiontypecode = st.code
		left join #dim_date dd
		on mob.mocreateddate = dd.date_id
	)

--==================================================================================================================================================
--=========================================================Final Transformation Process=============================================================

	select distinct * from
	(
		select 
			site_id
			,site_area
			,utcoffset
			,section
			,equipment_model 
			,equipment_number
			,mo_inspection_number
			,inspection_type
			,emol_number
			,emol_status
			,component
			,sub_component
			,[action]
			,[priority]
			,mo_type
			,submit_emol_date
			,emol_created_by
			,approval_date
			,approved_by
			,edd
			,mo_number 
			,mo_category
			,created_on
			,[year]
			,[month]
			,[week]
			,total_planned_costs
			,total_actual_costs
			,user_status
			,system_status
			,maintenance_activity_type
			,created_by
			,mo_teco_date
			,updated_by
			,aging_days
			,aging_range
			,status_equipment
			,status_follow_up
			,status_digital_planning
			,
			case 
				when status_mo = 'Closed' then 'Completed'
				when status_mo in ('Waiting Execution', 'Waiting Planning') then
					case 
						when aufnr is not null and ((lower(gr_status) in ('partial', 'full')) or (lower(gi_status) in ('partial', 'full'))) then 
							case 
								when gr_status is not null and gi_status is not null then 'Completed: ' + gr_status_txt + ', ' + gi_status_txt
								when gr_status is not null then 'Completed: ' + gr_status_txt
								when gi_status is not null then 'Completed: ' + gi_status_txt
							end
						when aufnr is not null and gr_status is null and gi_status is null then  'Not Completed'
						when aufnr is null then null
					end
				when status_mo = 'Waiting Part' then
					case 
						when aufnr is not null and ((lower(gr_status) = 'partial') or (lower(gi_status) = 'partial')) then 'Not Completed'
						when aufnr is not null and gr_status is null and gi_status is null then  'Not Completed'
						when aufnr is null then null
					end
				when status_mo = 'Waiting Approval' then null
			end as status_part
			,status_mo
			,
			row_number() over
			(
				partition by mo_number order by 
				case 
					when status_mo = 'Closed' then 1 
					when status_mo = 'Waiting Approval' then 2 
					when status_mo = 'Waiting Execution' then 3 
					when status_mo = 'Waiting Planning' then 4 
					when status_mo = 'Waiting Part' then 5 
				end asc
			) as status_mo_rank
		from
		(
			select 
				site_id
				,site_area
				,utcoffset
				,section
				,equipment_model 
				,equipment_number
				,mo_inspection_number
				,inspection_type
				,emol_number
				,emol_status
				,component
				,sub_component
				,[action]
				,[priority]
				,mo_type
				,submit_emol_date
				,emol_created_by
				,approval_date
				,approved_by
				,edd
				,mo_number 
				,mo_category
				,created_on
				,[year]
				,[month]
				,[week]
				,total_planned_costs
				,total_actual_costs
				,user_status
				,system_status
				,maintenance_activity_type
				,created_by
				,mo_teco_date
				,updated_by
				,aging_days
				,
				case 
					when aging_days between 0 and 14 then '1-14'
					when aging_days between 15 and 45 then '15-45'
					when aging_days > 45 then '>45'
				end as aging_range
				,status_equipment
				,status_follow_up
				,status_digital_planning
				,aufnr
				,gr_status
				,gi_status
				,gr_status_txt
				,gi_status_txt
				,
				case 
					when status_mo = 'Waiting Part' and mo_category = 'No Material' then 'Waiting Planning'
					else status_mo
				end as status_mo
			from 
			(
				select distinct
					bb.site_id
					,bb.site_area
					,bb.utcoffset
					,bb.section
					,bb.equipment_model 
					,bb.equipment_number
					,bo.mo_inspection_number
					,bo.inspection_type
					,bo.emol_number
					,bo.emol_status
					,bo.component
					,bo.sub_component
					,bo.[action]
					,bo.[priority]
					,bb.mo_type
					,dateadd(hour, bb.utcoffset, bo.submit_emol_date) as submit_emol_date
					,bo.emol_created_by
					,dateadd(hour, bb.utcoffset, bo.approval_date) as approval_date
					,bo.approved_by
					,bo.edd
					,bb.mo_number 
					,bb.mo_category
					,bb.created_on
					,bb.[year]
					,bb.[month]
					,bb.[week]
					,bb.total_planned_costs
					,bb.total_actual_costs
					,bb.user_status
					,bb.system_status
					,bb.maintenance_activity_type
					,bb.created_by
					,bb.mo_teco_date
					,bb.updated_by
					,bb.aging_days
					,bb.status_equipment
					,bb.status_follow_up
					,case when bd.value is not null then 'Yes' else 'No' end as status_digital_planning
					,cpo.monumber as aufnr
					,cpo.grstatus as gr_status
					,cpo.gistatus as gi_status
					,
					case 
					when cpo.grstatus is null then ''
					when lower(cpo.grstatus) = 'full' then 'GR Full'
					when lower(cpo.grstatus) = 'partial' then 'GR Partial'
					end gr_status_txt
					,
					case 
						when cpo.gistatus is null then ''
						when lower(cpo.gistatus) = 'full' then 'GI Full'
						when lower(cpo.gistatus) = 'partial' then 'GI Partial'
					end gi_status_txt
					,
					case
						when lower(bb.user_status) = 'comp' then 'Closed'
						when lower(bb.user_status) in ('init', 'wapv', 'inpv', 'nrev')then 'Waiting Approval'
						when lower(bb.user_status) = 'appv' and bd.value is not null then 'Waiting Execution'
						when lower(bb.user_status) = 'appv' and bd.value is null and cpo.monumber is not null and ((lower(cpo.grstatus) = 'full') or (lower(cpo.gistatus) in ('partial', 'full')))  then 'Waiting Planning'
						when lower(bb.user_status) = 'appv' and bd.value is null and cpo.monumber is not null and ((isnull(lower(cpo.grstatus), '') in ('', 'partial')) or (isnull(lower(cpo.gistatus), '') = ''))  then 'Waiting Part'
						when lower(bb.user_status) = 'appv' and bd.value is null and cpo.monumber is null then 'Waiting Planning'
					end status_mo
				from base_backlog bb
				left join base_order bo
				on bb.mo_number = bo.mo_number
				left join base_dplan bd
				on bb.mo_number = bd.value
				left join #checkpartorder cpo
				on bb.mo_number = cpo.monumber
			) a
			where [priority] is not null
		) a
	) a
	where status_mo_rank = 1

--==================================================================================================================================================
end
GO


