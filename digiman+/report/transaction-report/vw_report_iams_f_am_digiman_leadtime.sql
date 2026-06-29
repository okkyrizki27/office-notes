/****** Object:  View [am].[vw_report_iams_f_am_digiman_leadtime]    Script Date: 2026-06-17 13:57:20 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE view [am].[vw_report_iams_f_am_digiman_leadtime]
as
with workorder as
(
	select id, number, schedulestartdate, assetnumber, assetmodelcode,
	maintenancecategoryname, sitecode, isactive, sectiontypecode, duedate, status
	from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_execution/workorder/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[typecode] varchar(200),
		[number] varchar(16),
		[schedulestartdate] datetime,
		[assetnumber] varchar(200),
		[assetmodelcode] varchar(200),
		[maintenancecategoryname] varchar(512),
		[sitecode] varchar(64),
		[isactive] bit,
		[sectiontypecode] varchar(200),
		[duedate] datetime,
		[status] varchar(200)
	) as result
	where isactive = 1 and typecode = 'Inspection'
),
task as
(
	select id, workorderid from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_execution/task/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[workorderid] int,
		[type] varchar(200),
		[isactive] bit
	) as result
	where isactive = 1 and type = 'FlexiInspection'
),
taskpersonalized as
(

	select id, taskid, usercode, status, createdat, createdby,  modifiedat
	from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_execution/taskpersonalized/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[taskid] int,
		[usercode] varchar(128),
		[status] varchar(200),
		[createdat] datetime,
		[createdby] varchar(200),
		[modifiedat] datetime,
		[isactive] bit
	) as result
	where isactive = 1
),
taskpersonalizedfinding as
(
	select id, taskpersonalizedid from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_execution/taskpersonalizedfinding/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[taskpersonalizedid] int,
		[isactive] bit
	) as [result]
	where isactive=1
),
taskpersonalizedlog as
(
	select taskpersonalizedid, enddate, usercode from
	(
		select a.taskpersonalizedid, enddate, usercode,
		row_number() over(partition by a.taskpersonalizedid order by enddate desc) rank
		from
		(
			select taskpersonalizedid, enddate from openrowset
			(
				bulk 'assetmanagement/mkp/mkp_maintenance_execution/taskpersonalizedlog/',
				data_source = 'curated_dfs_core_windows_net',
				format = 'delta'
			)
			with
			(
				[taskpersonalizedid] int,
				[enddate] datetime,
				[isactive] bit
			) as result
			where isactive = 1
		) a
		inner join taskpersonalized b
		on a.taskpersonalizedid = b.id and b.status = 'Complete'
	) a
	where rank = 1
),
mechanicorderlist as
(
	select workorderid, taskpersonalizedfindingid, number, completedby, completeddate from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_order/mechanicorderlist/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[workorderid] int,
		[taskpersonalizedfindingid] int,
		[number] varchar(200),
		[completedby] varchar(200),
		[completeddate] datetime,
		[isactive] bit
	) as result
	where isactive = 1
),
workflowtransaction as
(
	select * from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_workflow/workflowtransaction/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[referencetransactionid] int,
		[status] varchar(32),
		[isactive] bit,
		[modifiedat] datetime,
		[modifiedby] varchar(200)
	) as result
	where status = 'Complete' and isactive = 1
),
assetmodel as
(
	select code, name from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/assetmodel/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(200)
	) as result
),
sectiontype as
(
	select code, name from openrowset
	(
		bulk 'assetmanagement/mkp/shared_tenant/sectiontype/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[tenantcode] varchar(64),
		[name] varchar(200),
		[isactive] bit
	) as result
	where isactive = 1 and tenantcode = 'MKP'
),
[user] as
(
	select code, fullname from openrowset
	(
		bulk 'assetmanagement/mkp/shared_user/user/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(128),
		[fullname] varchar(max)
	) as result
),
mapping_wo_status as
(
	select * from openrowset
	(
		bulk 'assetmanagement/mkp/mapping/config_mapping_wo_status.csv',
		data_source = 'config_dfs_core_windows_net',
		format = 'csv',
		parser_version = '2.0',
		first_row = 2
	)
	with
	(
		[status_code] varchar(5),
		[status_name] varchar(50),
		[status_mo_sap] varchar(15),
		[wo_status] varchar(15),
		[is_wo_overdue] bit,
		[check_taskpersonalized] bit,
		[taskpersonalized_status] varchar(15)
	) as result
),
config_wicope_manual as
(
	select
		name_id,
		[type_id],
		[site_id],
		[type_desc],
		[first_value] as [type_value],
		[type_status]
	from openrowset
	(
		bulk 'assetmanagement/mkp/mapping/config_wicope_manual.csv',
		data_source = 'config_dfs_core_windows_net',
		format = 'csv',
		parser_version = '2.0',
		first_row = 2
	)
	with
	(
		[name_id] [varchar](30),
		[type_id] [varchar](15),
		[site_id] [varchar](4),
		[type_desc] [varchar](255),
		[first_value] [varchar](30),
		[second_value] [varchar](30),
		[type_status] [varchar](30)
	) as [source]
	where [name_id] = 'TARGET_FULL_CYCLE' and [type_id] = 'TFC'
)


select distinct
	cast([date_id] as date) [date_id]
	,cast([mo_number] as varchar(25)) [mo_number]
	,cast([emol_number] as varchar(25)) [emol_number]
	,cast([maintenance_type] as varchar(512)) [maintenance_type]
	,cast([site_id] as varchar(10)) [site_id]
	,cast([section_name] as varchar(512)) [section_name]
	,cast([model_unit] as varchar(50)) [model_unit]
	,cast([equipment] as varchar(64)) [equipment]
	,cast([status] as varchar(50)) [status]
	,cast([schedule_date] as date) [schedule_date]
	,cast([assignment_date] as datetime) [assignment_date]
	,cast([assignmentby] as varchar(4000)) [assignmentby]
	,cast([leadtime_assignment] as numeric(132)) [leadtime_assignment]
	,cast([inspection_submitted_date] as datetime) [inspection_submitted_date]
	,cast([inspection_submittedby] as varchar(4000)) [inspection_submittedby]
	,cast([leadtime_inspection] as numeric(131)) [leadtime_inspection]
	,cast([submitted_emoldate] as datetime) [submitted_emoldate]
	,cast([submitted_emolby] as varchar(255)) [submitted_emolby]
	,cast([leadtime_create_emol] as numeric(131)) [leadtime_create_emol]
	,cast([approved_date] as datetime) [approved_date]
	,cast([approvedby] as varchar(4000)) [approvedby]
	,cast([leadtime_approval] as numeric(131)) [leadtime_approval]
	,cast([leadtime_ordering] as numeric(131)) [leadtime_ordering]
	,cast([fullcycle_leadtime] as numeric(131)) [fullcycle_leadtime]
	,cast([fullcycle_leadtime_target] as varchar(255)) [fullcycle_leadtime_target]
	,cast([load_date] as datetime) [load_date]
from
(
	select a.*,
	first_value(a.status_name) over(partition by a.Id, a.TaskId, a.TaskPersonalizedId order by a.status_code asc) status
	from

	(
		select
			 wo.id as Id,
			 t.id as TaskId,
			 tp.id as TaskPersonalizedId,
			 wo.schedulestartdate as date_id
			,wo.number as mo_number
			,mol.number as emol_number
			,wo.maintenancecategoryname as maintenance_type
			,wo.sitecode as site_id
			,st.name as section_name
			,asm.name as model_unit
			,wo.assetnumber as equipment
			--,first_value(mws.status_name) over(partition by wo.id, t.id, tp.id order by mws.status_code asc) as status
			,wo.schedulestartdate as schedule_date
			,tp.createdat as assignment_date
			,usr1.fullname as assignmentby -- tp.usercode
			,round(datediff(second, wo.schedulestartdate, tp.createdat) / 3600.0, 2) as leadtime_assignment
			,tpl.enddate as inspection_submitted_date
			,tpl.usercode as inspection_submittedby
			,round(datediff(second, tp.createdat, tpl.enddate) / 3600.0, 2) as leadtime_inspection
			,mol.completeddate as submitted_emoldate
			,usr2.fullname as submitted_emolby -- mol.completedby
			,round(datediff(second, tpl.enddate, mol.completeddate) / 3600.0, 2) as leadtime_create_emol
			,wft.modifiedat as approved_date
			,usr3.fullname as approvedby -- wft.modifiedby
			,round(datediff(second, mol.completeddate, wft.modifiedat) / 3600.0, 2) as leadtime_approval
			,round(datediff(second, tpl.enddate,  wft.modifiedat) / 3600.0, 2) as leadtime_ordering
			,round(datediff(second, tp.createdat,  wft.modifiedat) / 3600.0, 2) as fullcycle_leadtime
			,cwm.type_desc as fullcycle_leadtime_target
			,dateadd(hour,7, getutcdate())as load_date
			,case when wo.[status] ='Cancelled' then 'Cancelled' else mws.status_code end status_code
			,case when wo.[status] ='Cancelled' then 'Cancelled' else mws.status_name end status_name
			,case
				when wo.[status] ='Cancelled'  then 1
				when mws.check_taskpersonalized = 0 then 1
				when mws.check_taskpersonalized = 1 then
					case
						when tp.status = mws.taskpersonalized_Status
						and
						case
							when (case when wo.duedate >= cast(getutcdate() as date) then 0 when wo.duedate < cast(getutcdate() as date) then 1 end = mws.is_wo_overdue) then 1
							else  0
						end = 1
						then 1 else 0 end
			end correct_status
		from workorder wo
		inner join task as t
		on wo.id  = t.workorderid
		left join taskpersonalized as tp
		on t.id = tp.taskid
		left join taskpersonalizedfinding as tpf
		on tp.id = tpf.taskpersonalizedid
		left join taskpersonalizedlog as tpl
		on tp.id = tpl.taskpersonalizedid
		left join mechanicorderlist as mol
		on wo.id = mol.workorderid and tpf.id = mol.taskpersonalizedfindingid
		inner join workflowtransaction as wft
		on wo.id = wft.referencetransactionid
		left join sectiontype as st
		on wo.sectiontypecode = st.code
		left join assetmodel as asm
		on wo.assetmodelcode = asm.code
		left join [user] as usr1
		on tp.usercode = usr1.code
		left join [user] as usr2
		on mol.completedby = usr2.code
		left join [user] as usr3
		on wft.modifiedby = usr3.code
		left join config_wicope_manual cwm
		on wo.sitecode = cwm.site_id and lower(st.name) = lower(cwm.type_status)
		left join mapping_wo_status as mws
		on wo.status = mws.wo_status
	) a
	where correct_status = 1
) a

GO
