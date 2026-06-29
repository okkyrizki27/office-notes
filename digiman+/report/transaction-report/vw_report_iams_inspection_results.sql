/****** Object:  View [am].[vw_report_iams_inspection_results]    Script Date: 2026-06-17 13:59:16 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE view [am].[vw_report_iams_inspection_results]
as
with workorder as
(
	select id, number, schedulestartdate, [source], enddate, assetnumber,
	assetmodelcode, maintenancecategoryname, sectiontypecode, sitecode
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
		[source] varchar(200),
		[status] varchar(200),
		[enddate] datetime,
		[assetnumber] varchar(200),
		[assetmodelcode] varchar(200),
		[maintenancecategoryname] varchar(512),
		[sectiontypecode] varchar(200),
		[sitecode] varchar(64),
		[isactive] bit
	) as [result]
	where isactive = 1 and typecode = 'Inspection' and [status] not in ('Close', 'Cancelled')
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
		[status] varchar(200),
		[isactive] bit
	) as [result]
	where isactive = 1 and type = 'FlexiInspection' and [status] not in ('Close', 'Cancelled')
),
taskpersonalized as
(
	select id, taskid, usercode from openrowset
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
		[isactive] bit
	) as [result]
	where isactive = 1 and [status] = 'Complete'
),
taskpersonalizedfinding as (
	select id, componentcode, othersubcomponentname, subcomponentcode, defectnotes,
	taskpersonalizedid, damagecode, actionremedycode, isimmediateexecutable, prioritycode from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_execution/taskpersonalizedfinding/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[componentcode] varchar(64),
		[othersubcomponentname] varchar(512),
		[subcomponentcode] varchar(64),
		[defectnotes] varchar(1024),
		[taskpersonalizedid] int,
		[damagecode] varchar(64),
		[actionremedycode] varchar(64),
		[isimmediateexecutable] bit,
		[prioritycode] varchar(64),
		[isactive] bit
	) as [result]
	where isactive = 1
),
[user] as
(
	select fullname, code from openrowset
	(
		bulk 'assetmanagement/mkp/shared_user/user/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[fullname] varchar(max),
		[code] varchar(128)
	) as [result]
),
[site] as
(
	select [name], utcoffset, code from openrowset
	(
		bulk 'assetmanagement/mkp/shared_tenant/site/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[tenantcode] varchar(64),
		[name] varchar(100),
		[utcoffset] int,
		[isactive] bit
	) as [result]
	where isactive = 1 and tenantcode = 'MKP'
),
assetmodel as
(
	select [name], code from openrowset
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
component as
(
	select code, [name] from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/component/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(200)
	) as [result]
),
subcomponent as (
	select [name], code from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/subcomponent/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(200)
	) as [result]
),
damagecode as
(
	select code, damagegroupcode, [name], [description]  from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/damagecode/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[damagegroupcode] varchar(64),
		[name] varchar(200),
		[description] varchar(max)
	) as [result]
),
damagegroup as
(
	select code, [name], [description] from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/damagegroup/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(200),
		[description] varchar(max)
	) as [result]
),
actionremedy as
(
	select [name], code from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/actionremedy/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(200)
	) as [result]
),
[priority] as
(
	select code, concat([name], ' ', [description]) priorityname from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/priority/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(15),
		[group] varchar(64),
		[description] varchar(max)
	) as [result]
	where [group] = 'Inspection'
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
damagecodegroup as
(
	select dc.code as damagecode, dc.[name] as damagecodename, dc.[description] as damagecodedesc,
	dg.code as damagegroupcode, dg.[name] as damagegroupname, dg.[description] as damagegroupdesc
	from damagecode dc
	inner join damagegroup dg
	on dc.damagegroupcode = dg.code
)

select
	cast([Date] as datetime) [Date]
	,cast([SubmittedUtcDate] as datetime) [SubmittedUtcDate]
	,cast([MONo] as varchar(16)) [MONo]
	,cast([InspectionType] as varchar(512)) [InspectionType]
	,cast([Equipment] as varchar(64)) [Equipment]
	,cast([ResultId] as int) [ResultId]
	,cast([InspectorName] as varchar(1000)) [InspectorName]
	,cast([ModelName] as varchar(512)) [ModelName]
	,cast([RouteId] as int) [RouteId]
	,cast([RouteCode] as varchar(255)) [RouteCode]
	,cast([RouteName] as varchar(255)) [RouteName]
	,cast([ComponentId] as int) [ComponentId]
	,cast([ComponentCode] as varchar(4)) [ComponentCode]
	,cast([ComponentName] as varchar(512)) [ComponentName]
	,cast([SubComponentId] as int) [SubComponentId]
	,cast([SubComponentOther] as varchar(128)) [SubComponentOther]
	,cast([SubcomponentCode] as varchar(512)) [SubcomponentCode]
	,cast([SubcomponentName] as varchar(512)) [SubcomponentName]
	,cast([DamageGroupId] as int) [DamageGroupId]
	,cast([DamageGroupCode] as varchar(16)) [DamageGroupCode]
	,cast([DamageGroupName] as varchar(512)) [DamageGroupName]
	,cast([DamageGroupDescription] as varchar(512)) [DamageGroupDescription]
	,cast([DamageCodeId] as int) [DamageCodeId]
	,cast([DamageCode] as varchar(16)) [DamageCode]
	,cast([DamageCodeName] as varchar(512)) [DamageCodeName]
	,cast([DamageCodeDescription] as varchar(512)) [DamageCodeDescription]
	,cast([ModelRouteText] as varchar(1024)) [ModelRouteText]
	,cast([Condition] as varchar(2)) [Condition]
	,cast([ConditionName] as varchar(512)) [ConditionName]
	,cast([ActionId] as int) [ActionId]
	,cast([ActionName] as varchar(128)) [ActionName]
	,cast([PriorityId] as varchar(10)) [PriorityId]
	,cast([PriorityName] as varchar(512)) [PriorityName]
	,cast([Notes] as varchar(512)) [Notes]
	,cast([SiteName] as varchar(1000)) [SiteName]
	,cast([SectionTypeName] as varchar(512)) [SectionTypeName]
	,cast([SourceCode] as varchar(8)) [SourceCode]
	,cast([ScheduleDate] as date) [ScheduleDate]
from
(
	select distinct
		dateadd(hour,st.utcoffset , wo.enddate) as [Date],
		wo.enddate as SubmittedUtcDate,
		wo.number as MONo,
		wo.maintenancecategoryname as InspectionType,
		wo.assetnumber as Equipment,
		tpf.id as ResultId,
		u.fullname as InspectorName,
		asm.name as ModelName,
		null as RouteId,
		null as RouteCode,
		null as RouteName,
		null as ComponentId,
		tpf.componentcode as ComponentCode,
		co.[name] as ComponentName,
		null as SubComponentId,
		tpf.othersubcomponentname as SubComponentOther,
		tpf.subcomponentcode as SubcomponentCode,
		sc.name as SubcomponentName,
		null as DamageGroupId,
		dcg.damagegroupcode as DamageGroupCode,
		dcg.damagegroupname as DamageGroupName,
		dcg.damagegroupdesc as DamageGroupDescription,
		null as DamageCodeId,
		tpf.damagecode as DamageCode,
		dcg.damagecodename as DamageCodeName,
		dcg.damagecodedesc as DamageCodeDescription,
		null as ModelRouteText,
		null as Condition,
		null as ConditionName,
		null as ActionId,
		ar.[name] as ActionName,
		case when tpf.isimmediateexecutable = 1 and isnull(tpf.prioritycode, '') = '' then 'CLOSE' else pr.code end PriorityId,
		case when tpf.isimmediateexecutable = 1 and isnull(tpf.prioritycode, '') = '' then 'CLOSE' else pr.priorityname end PriorityName,
		case when tpf.isimmediateexecutable = 1 and isnull(tpf.prioritycode, '') = '' then concat('CLOSE - ', tpf.defectnotes) else tpf.defectnotes end Notes,
		st.[name] as SiteName,
		sty.[name] as SectionTypeName,
		wo.[source] as SourceCode,
		wo.schedulestartdate as ScheduleDate
	from workorder wo
		inner join task t
		on t.workorderid = wo.id
		left join taskpersonalized tp
		on tp.taskid = t.id
		left join taskpersonalizedfinding tpf
		on tpf.taskpersonalizedid = tp.id
		left join [site] st
		on wo.sitecode = st.code
		left join [user] u
		on tp.usercode = u.code
		left join [assetmodel] asm
		on wo.assetmodelcode = asm.code
		left join [component] as co
		on tpf.componentcode = co.code
		left join damagecodegroup as dcg
		on tpf.damagecode = dcg.damagecode
		left join subcomponent as sc
		on tpf.subcomponentcode = sc.code
		left join actionremedy as ar
		on tpf.actionremedycode = ar.code
		left join [priority] as pr
		on tpf.prioritycode = pr.code
		left join sectiontype as sty
		on wo.sectiontypecode = sty.code
	where tpf.id is not null
) a
GO
