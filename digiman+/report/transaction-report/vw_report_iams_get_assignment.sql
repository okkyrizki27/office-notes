/****** Object:  View [am].[vw_report_iams_get_assignment]    Script Date: 2026-06-17 13:58:09 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE view [am].[vw_report_iams_get_assignment]
as
with workorder as
(
	select id, number, duedate, [status] from openrowset
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
		[duedate] datetime,
		[status] varchar(200),
		[isactive] bit
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
	select id, taskid, usercode, [status], createdby, createdat, modifiedat from openrowset
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
		[isactive] bit,
		[createdby] varchar(200),
		[createdat] datetime,
		[modifiedat] datetime
	) as [result]
	where isactive = 1
),
taskpersonalizedlog as
(
	select a.taskpersonalizedid, max(a.enddate) enddate from
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
		) as [result]
		where isactive = 1
	) a
	inner join taskpersonalized b
	on a.taskpersonalizedid = b.[id] and b.[status] = 'Complete'
	group by a.taskpersonalizedid
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
		FORMAT = 'csv',
		PARSER_VERSION = '2.0',
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
userinformation as
(
	select b.siteid, a.code, b.employeeid, a.fullname from [user] a
	left join useremploymentprofile b
	on a.code = b.usercode
)


select
	cast([MOId] as int) [MOId]
	,cast([InspectorId] as varchar(255)) [InspectorId]
	,cast([InspectorName] as varchar(1000)) [InspectorName]
	,cast([CreatedUtcDate] as datetime) [CreatedUtcDate]
	,cast([CreatedUtcDate22] as datetime) [CreatedUtcDate22]
	,cast([SubmittedUtcDate] as datetime) [SubmittedUtcDate]
	,cast([SubmittedUtcDate2] as datetime) [SubmittedUtcDate2]
	,cast([CompletedUtcDate] as datetime) [CompletedUtcDate]
	,cast([CompletedUtcDate22] as datetime) [CompletedUtcDate22]
	,cast([Status] as varchar(8)) [Status]
	,cast([StatusName] as varchar(512)) [StatusName]
	,cast([SPVid] as varchar(255)) [SPVid]
	,cast([SPVName] as varchar(1000)) [SPVName]
	,cast(null as varchar(5000)) [Notes]
	,cast([MONo] as varchar(16)) [MONo]
from
(
	select a.*,
	first_value(a.status_code) over(partition by a.MOId, a.TaskId, a.TaskPersonalizedId order by a.status_code asc) [Status],
	first_value(a.status_name) over(partition by a.MOId, a.TaskId, a.TaskPersonalizedId order by a.status_code asc) StatusName
	from
	(
		select a.*,
			case when a.wo_status ='Cancelled' then 'Cancelled' else b.status_code end status_code,
			case when a.wo_status ='Cancelled' then 'Cancelled' else b.status_name end status_name,
			case
				when a.wo_status ='Cancelled'  then 1
				when b.check_taskpersonalized = 0 then 1
				when b.check_taskpersonalized = 1 then
					case
						when a.taskpersonalized_status = b.taskpersonalized_status
						and
						case
							when (case when a.duedate >= a.currentdate then 0 when a.duedate < a.currentdate then 1 end = b.is_wo_overdue) then 1
							else  0
						end = 1
						then 1 else 0 end
			end correct_status
		from
		(
			select a.id MOId, b.id TaskId, c.id TaskPersonalizedId, a.status wo_status, d.employeeid InspectorId, d.fullname InspectorName, c.status taskpersonalized_status,
			dateadd(hour, e.utcoffset, c.createdat) CreatedUtcDate, c.createdat CreatedUtcDate22,
			dateadd(hour, e.utcoffset, f.enddate) SubmittedUtcDate,  f.enddate SubmittedUtcDate2,
			cast(dateadd(hour, e.utcoffset, a.duedate) as date) duedate, cast(dateadd(hour, e.utcoffset, getutcdate()) as date) currentdate,
			null CompletedUtcDate,
			null CompletedUtcDate22,
			g.employeeid SPVid, g.fullname SPVName, a.number MONo
			from workorder a
			inner join task b
			on a.id = b.workorderid
			left join taskpersonalized c
			on b.id = c.taskid
			left join userinformation d
			on c.usercode = d.code
			left join [site] e
			on d.siteid = e.code
			left join taskpersonalizedlog f
			on c.id = f.taskpersonalizedid
			left join userinformation g
			on c.createdby = g.code
		) a
		left join mapping_wo_status b
		on a.wo_status = b.wo_status
	) a
	where correct_status = 1
) a
GO
