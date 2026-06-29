/****** Object:  View [am].[vw_report_iams_get_molist]    Script Date: 2026-06-17 13:58:48 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE view [am].[vw_report_iams_get_molist]
as
with workorder as
(
	select id, number, [description], schedulestartdate, assetnumber, assetmodelcode,
	maintenancecategorycode, maintenancecategoryname, sitecode, isactive, createdat,
	modifiedat, sectiontypecode, duedate, [status], typecode
	from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_execution/workorder/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[number]varchar(16),
		[description] varchar(512),
		[schedulestartdate] datetime,
		[assetnumber] varchar(200),
		[assetmodelcode] varchar(200),
		[maintenancecategorycode] varchar(200),
		[maintenancecategoryname] varchar(512),
		[sitecode] varchar(64),
		[isactive] bit,
		[createdat] datetime,
		[modifiedat] datetime,
		[sectiontypecode] varchar(200),
		[duedate] datetime,
		[status] varchar(200),
		[typecode] varchar(200)
	) as [result]
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
	) as [result]
	where isactive = 1 and type = 'FlexiInspection'
),
taskpersonalized as
(

	select id, usercode, [status], createdby, taskid, modifiedat, createdat,
	min(case when [status] not in ('Closed','Cancelled') then createdat end) over(partition by taskid) as mincreatedat
	from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_execution/taskpersonalized/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[usercode] varchar(128),
		[status] varchar(200),
		[createdby] varchar(200),
		[taskid] int,
		[modifiedat] datetime,
		[isactive] bit,
		[createdat] datetime
	) as [result]
	where isactive = 1
),
asset as
(
	select assetnumber, assetcategorycode, assetmodelcode from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/asset/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[assetnumber] varchar(200),
		[assetcategorycode] varchar(64),
		[assetmodelcode] varchar(64)
	) as [result]
),
assetmodel as
(
	select code, [name] from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/assetmodel/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(200)
	) as [result]
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
		[fullname] varchar(max),
		[isactive] bit
	)  as [result]
	where isactive = 1
),
useremploymentprofile as
(
	select usercode, employeeid, siteid from openrowset
	(
		bulk 'assetmanagement/mkp/shared_user/useremploymentprofile/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[usercode] varchar(128),
		[employeeid] varchar(max),
		[siteid] varchar(max)
	)	as [result]
),
[site] as
(
	select code, utcoffset from openrowset
	(
		bulk 'assetmanagement/mkp/shared_tenant/site/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[tenantcode] varchar(64),
		[utcoffset] int,
		[isactive] bit
	)as [result]
	where isactive = 1 and tenantcode = 'MKP'
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
		status_code varchar(5),
		status_name varchar(50),
		status_mo_sap varchar(15),
		wo_status varchar(15),
		is_wo_overdue bit,
		check_taskpersonalized bit,
		taskpersonalized_status varchar(15)
	) as [result]
),
unit as
(
	select assetnumber, assetcategorycode, assetmodelcode, asm.name as assetmodelname from asset ase
	left join assetmodel asm
	on ase.assetmodelcode = asm.code
),
userinformation as
(
	select b.siteid, a.code, b.employeeid, a.fullname from [user] a
	left join useremploymentprofile b
	on a.code = b.usercode
)


select
	cast([Id] as int) [Id]
	,cast([MONo] as varchar(16)) [MONo]
	,cast([MOName] as varchar(512)) [MOName]
	,cast([ScheduleDate] as date) [ScheduleDate]
	,cast([MOUtcDate] as date) [MOUtcDate]
	,cast([Equipment] as varchar(64)) [Equipment]
	,cast([WorkCenter] as varchar(16)) [WorkCenter]
	,cast([ModelName] as varchar(50)) [ModelName]
	,cast([AUART] as varchar(16)) [AUART]
	,cast([ILART] as varchar(6)) [ILART]
	,cast([ILARTText] as varchar(512)) [ILARTText]
	,cast([TXT04] as varchar(8)) [TXT04]
	,cast([ARBPL] as varchar(16)) [ARBPL]
	,cast([EQTYP] as varchar(3)) [EQTYP]
	,cast([ATWRT] as varchar(64)) [ATWRT]
	,cast([SiteId] as varchar(10)) [SiteId]
	,cast([WeekAge] as int) [WeekAge]
	,cast([QMNUM] as varchar(32)) [QMNUM]
	,cast([QMTXT] as varchar(512)) [QMTXT]
	,cast([HDDTL] as varchar(3)) [HDDTL]
	,cast([InspectionStatus] as varchar(8)) [InspectionStatus]
	,cast([IsActive] as bit) [IsActive]
	,cast([CreatedUtcDate] as datetime) [CreatedUtcDate]
	,cast([ModifiedUtcDate] as datetime) [ModifiedUtcDate]
	,cast([StatusName] as varchar(512)) [StatusName]
	,cast([AssignedBy] as varchar(255)) [AssignedBy]
	,cast([SectionTypeName] as varchar(512)) [SectionTypeName]
	,cast([DateCompletion] as datetime) [DateCompletion]
from
(
	select a.*,
		first_value(a.status_code) over(partition by a.Id, a.TaskId, a.TaskPersonalizedId order by a.status_code asc) InspectionStatus,
		first_value(a.status_name) over(partition by a.Id, a.TaskId, a.TaskPersonalizedId  order by a.status_code asc) StatusName
	from
	(

		select
			wo.id as Id,
			t.id as TaskId,
			tp.id as TaskPersonalizedId,
			wo.number as MONo,
			wo.[description] as MOName,
			wo.schedulestartdate as ScheduleDate,
			wo.schedulestartdate as MOUtcDate,
			wo.assetnumber as Equipment,
			null as WorkCenter,
			un.assetmodelname as ModelName,
			null as AUART,
			wo.maintenancecategorycode as ILART,
			wo.maintenancecategoryname as ILARTText,
			null as TXT04,
			null as ARBPL,
			un.assetcategorycode as EQTYP,
			st.[name] as ATWRT,
			wo.sitecode as SiteId,
			null as WeekAge,
			null as QMNUM,
			null as QMTXT,
			null as HDDTL,
			wo.isactive as IsActive,
			wo.createdat as CreatedUtcDate,
			wo.modifiedat as ModifiedUtcDate,
			ui.employeeid as AssignedBy,
			st.[name] as SectionTypeName,
			case
				when lower(tp.[status]) = 'complete' then tp.modifiedat
				when lower(tp.[status]) in ('open', 'in progress', 'pending') then tp.mincreatedat
				else wo.duedate
			end as DateCompletion,
			case when wo.[status] ='Cancelled' then 'Cancelled' else mws.status_code end status_code,
			case when wo.[status] ='Cancelled' then 'Cancelled' else mws.status_name end status_name,
			case
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
		from workorder as wo
			inner join task as t
			on t.workorderid = wo.id
			left join taskpersonalized as tp
			on t.id = tp.taskid
			left join unit as un
			on wo.assetnumber = un.assetnumber and wo.assetmodelcode = un.assetmodelcode
			left join sectiontype as st
			on wo.sectiontypecode = st.code
			left join userinformation as ui
			on tp.usercode = ui.code
			left join mapping_wo_status as mws
			on wo.[status] = mws.wo_status
	) a
	where correct_status = 1
) a
GO
