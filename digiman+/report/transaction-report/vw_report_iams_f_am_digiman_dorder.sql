/****** Object:  View [am].[vw_report_iams_f_am_digiman_dorder]    Script Date: 2026-06-17 13:53:40 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



CREATE view [am].[vw_report_iams_f_am_digiman_dorder]
as
--=========================================================IAMS Digiman-DOrder Source========================================================
with moapproval as
(
	select monumber, mostatus, approval1date, approval2date from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_dexecute/moapproval/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[monumber] varchar(50),
		[mostatus] varchar(50),
		[approval1date] varchar(50),
		[approval2date] varchar(50)
	) as [result]
),

--==================================================================================================================================================
--=========================================================IAMS Maintencane-Execution Source========================================================
workorder as
(
	select id, number, assetnumber, assetmodelcode, maintenancecategorycode, maintenancecategoryname, sitecode, sectiontypecode
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
		[assetnumber] varchar(200),
		[assetmodelcode] varchar(200),
		[maintenancecategorycode] varchar(200),
		[maintenancecategoryname] varchar(512),
		[sitecode] varchar(64),
		[isactive] bit,
		[sectiontypecode] varchar(200)
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
		[isactive] bit
	) as result
	where isactive = 1
),
taskpersonalizedfinding as
(
	select id, taskpersonalizedid, componentcode, subcomponentcode, othersubcomponentname, damagecode, actionremedycode, prioritycode
	from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_execution/taskpersonalizedfinding/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[taskpersonalizedid] int,
		[componentcode] varchar(64),
		[subcomponentcode] varchar(64),
		[othersubcomponentname] varchar(512),
		[damagecode] varchar(64),
		[actionremedycode] varchar(64),
		[prioritycode] varchar(64),
		[isactive] bit
	) as [result]
	where isactive = 1
),

--==================================================================================================================================================
--=========================================================IAMS Maintencane-Order Source============================================================

checkpartorder as
(
	select id, assetnumber, sitecode, reservationnumber, materialnumber, reservationquantity, gidate, monumber, modescription, [status],
	grstatus, gistatus
	from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_order/checkpartorder/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[assetnumber] varchar(200),
		[sitecode] varchar(64),
		[reservationnumber] int,
		[materialnumber] varchar(50),
		[reservationquantity] float,
		[gidate] varchar(16),
		[monumber] varchar(50),
		[modescription] varchar(250),
		[status] varchar(16),
		[grstatus] varchar(64),
		[gistatus] varchar(64),
		[isactive] bit
	) as result
	where isactive = 1
),
material as
(
	select number, ranking, siteid from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_order/material/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[number] varchar(200),
		[ranking] varchar(64),
		[siteid] varchar(64),
		[isactive] bit
	) as result
	where isactive = 1
),
mechanicorderdetail as
(
	select id, mechanicorderlistid, componentcode, subcomponentcode, othersubcomponentname, damagecode,
	actionremedycode, prioritycode, createdby from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_order/mechanicorderdetail/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[mechanicorderlistid] int,
		[componentcode] varchar(64),
		[subcomponentcode] varchar(64),
		[othersubcomponentname] varchar(512),
		[damagecode] varchar(64),
		[actionremedycode] varchar(64),
		[prioritycode] varchar(64),
		[createdby] varchar(128),
		[isactive] bit
	) as result
	where isactive = 1
),
mechanicorderlist as
(
	select id, costtypecode, workorderid, taskpersonalizedfindingid, mechanicordersummaryid, number, edd, [status],
	deletereason, createdby, createdat, modifiedby, isactive from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_order/mechanicorderlist/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[costtypecode] varchar(64),
		[workorderid] int,
		[taskpersonalizedfindingid] int,
		[mechanicordersummaryid] int,
		[number] varchar(200),
		[edd] datetime,
		[status] varchar(200),
		[deletereason] varchar(max),
		[createdby] varchar(128),
		[createdat] datetime,
		[modifiedby] varchar(128),
		[isactive] bit
	) as result
	--where isactive = 1
),
mechanicordermaterial as
(
	select id, mechanicorderlistid, batchcode, quantity, uomcode, totalcost, materialdescription, materialnumber, materialranking, createdat, isactive
	from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_order/mechanicordermaterial/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[mechanicorderlistid] int,
		[batchcode] varchar(64),
		[quantity] numeric(18,2),
		[uomcode] varchar(64),
		[totalcost] numeric(18,2),
		[materialdescription] varchar(200),
		[materialnumber] varchar(200),
		[materialranking] varchar(64),
		[createdat] datetime,
		[isactive] bit
	) as result
	where isactive = 1
),
mechanicordersummary as
(
	select id, assetnumber, maintenancecategorycode, sectiontypecode, sitecode, number
	from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_order/mechanicordersummary/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[assetnumber] varchar(200),
		[maintenancecategorycode] varchar(64),
		[sectiontypecode] varchar(200),
		[sitecode] varchar(64),
		[number] varchar(200),
		[isactive] bit
	) as result
	where isactive = 1
),
poolingmoitem as
(
	select poolingid, basicstartdate, materialnumber, materialquantity, batch, emolnumber, isactive from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_order/poolingmoitem/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[poolingid] int,
		[basicstartdate] datetime,
		[materialnumber] varchar(50),
		[materialquantity] varchar(50),
		[batch] varchar(20),
		[emolnumber] varchar(50),
		[isactive] bit
	) as result
	where isactive = 1
),
sapmosyncorder as
(
	select id, poolingid, mono, poolingstatus, sapstatus, saptext, createdutcdate, modifiedutcdate from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_maintenance_order/sapmosyncorder/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[id] int,
		[poolingid] int,
		[mono] varchar(32),
		[poolingstatus] varchar(6),
		[sapstatus] smallint,
		[saptext] varchar(1024),
		[createdutcdate] datetime,
		[modifiedutcdate] datetime
	) as result
),

--==================================================================================================================================================
--=========================================================IAMS Services Asset Source===============================================================
actionremedy as
(
	select code, name from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/actionremedy/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(200),
		[isactive] bit
	) as result
	where isactive = 1
),
asset as
(
	select assetnumber, assetmodelcode from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/asset/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[assetnumber] varchar(200),
		[assetmodelcode] varchar(64),
		[isactive] bit
	) as result
	where isactive = 1
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
		[name] varchar(200),
		[isactive] bit
	) as result
	where isactive = 1
),
component as
(
	select code, name from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/component/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(200),
		[isactive] bit
	) as result
	where isactive = 1
),
damagecode as
(
	select code, damagegroupcode, name from openrowset
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
		[isactive] bit
	) as result
	where isactive = 1
),
damagegroup as
(
	select code, name from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/damagegroup/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(200),
		[isactive] bit
	) as result
	where isactive = 1
),
[priority] as
(
	select code, [group], [name], [description] from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/priority/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[group] varchar(64),
		[name] varchar(15),
		[description] varchar(max),
		[isactive] bit
	) as result
	where isactive = 1
),
subcomponent as
(
	select code, name from openrowset
	(
		bulk 'assetmanagement/mkp/mkp_services_asset/subcomponent/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(200),
		[isactive] bit
	) as result
	where isactive = 1
),
--==================================================================================================================================================
--=========================================================IAMS Workflow Source=====================================================================

workflowtransaction as
(
	select referencetransactionid, [status], modifiedat, modifiedby from openrowset
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
	where isactive = 1
),

--==================================================================================================================================================
--=========================================================Shared Tenant Source=====================================================================

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
[site] as
(
	select code, name, utcoffset from openrowset
	(
		bulk 'assetmanagement/mkp/shared_tenant/site/',
		data_source = 'curated_dfs_core_windows_net',
		format = 'delta'
	)
	with
	(
		[code] varchar(64),
		[name] varchar(100),
		[utcoffset] int,
		[isactive] bit
	) as result
	where isactive = 1
),


--==================================================================================================================================================
--=========================================================Shared User Source=======================================================================

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
	) as result
	where isactive = 1
),

--==================================================================================================================================================
--=========================================================Mapping Data Source=======================================================================
mapping_mol_status as
(
	select * from openrowset
	(
		bulk 'assetmanagement/mkp/mapping/config_mapping_mol_status.csv',
		data_source = 'config_dfs_core_windows_net',
		format='csv',
		parser_version='2.0',
		firstrow=2
	)
	with
	(
		[status] varchar(10),
		[status_name] varchar(30),
		[status_desc] varchar(40),
		[mol_status] varchar(30),
		[is_active] bit,
		[workflow_transaction_status] varchar(30),
		[require_mono] bit
	) as result
),

mapping_pooling_validation as
(
	select * from openrowset
	(
		bulk 'assetmanagement/mkp/mapping/config_mapping_pooling_validation.csv',
		data_source = 'config_dfs_core_windows_net',
		format='csv',
		parser_version='2.0',
		firstrow=2
	)
	with
	(
		[id] int,
		[issameequipment] int,
		[issamematerialnumber] int,
		[ismaterialrankinga] int,
		[ismaterialrankingb] int,
		[ismaterialrankingc] int,
		[ismaterialrankingd] int,
		[ismaterialrankinge] int,
		[ismotrackingctrd] int,
		[ismotrackingrel] int,
		[ismotrackingteco] int,
		[ismotrackingclsd] int,
		[issamematerialqty] int,
		[isgrstatuspartial] int,
		[isgrstatusfull] int,
		[isgistatuspartial] int,
		[isgistatusfull] int,
		[isvalidgidate] int,
		[emolstatus] varchar(5),
		[poolingstatus] varchar(5),
		[canactiondigimandelete] int,
		[canactionsappushdelete] int,
		[cancreatemo] int,
		[cancreatemowithnote] int,
		[colorcategory] varchar(10),
		[remark] varchar(500)
	) as result
),
--==================================================================================================================================================
--=========================================================Transformation Process===================================================================

maintenance_execution_transformation as
(
	select
		wo.id as workorderid
		,tpf.id as taskpersonalizedfindingid
		,tpf.taskpersonalizedid as taskpersonalizedid
		,wo.number as mono
		,wo.maintenancecategorycode as inspectiontype
		,wo.assetnumber as assetnumber
		,tp.usercode as usercode
		,tpf.componentcode as componentcode
		,tpf.subcomponentcode as subcomponentcode
		,tpf.othersubcomponentname as othersubcomponentname
		,tpf.actionremedycode as actionremedycode
		,tpf.prioritycode as prioritycode
		,tpf.damagecode as damagecode
		,wo.sectiontypecode as sectiontypecode
		,wo.sitecode as sitecode
	from workorder wo
	inner join task t
	on wo.id = t.workorderid
	left join taskpersonalized as tp
	on t.id = tp.taskid
	left join taskpersonalizedfinding as tpf
	on tp.id = tpf.taskpersonalizedid
),
maintenance_order_transformation as
(
	select * from
	(
		select
			case when mos.id is null then 0 else 1 end summaryreference
			,mol.workorderid
			,mol.taskpersonalizedfindingid
			,mod.id as mechanicorderdetailid
			,mom.id as mechanicordermaterialid
			,cast(mol.createdat as date) as date_id
			,mos.number as mono
			,mos.maintenancecategorycode as inspectiontype
			,mos.assetnumber as assetnumber
			,mod.createdby as usercode
			,mod.componentcode as componentcode
			,mod.subcomponentcode as subcomponentcode
			,mod.othersubcomponentname as othersubcomponentname
			,mod.actionremedycode as actionremedycode
			,mod.prioritycode as prioritycode
			,mod.damagecode as damagecode
			,mos.sectiontypecode as sectiontypecode
			,mos.sitecode as sitecode
			,mol.createdat as submittedutcdateutc
			,mol.createdat as submittedutcdate
			,datediff(day, cast(mol.createdat as date), cast(getutcdate() as date)) aging
			,mol.number as emolno
			,mol.id as detailid
			,mol.edd as eddmol
			,mol.costtypecode as motype
			,mol.deletereason as deletereason
			,mom.materialnumber as materialnumber
			,mom.materialdescription as materialdescription
			,mom.quantity as quantity
			,mom.uomcode as unit
			,mom.materialranking as materialranking
			,mom.batchcode as batch
			,mol.createdat as submitdate
			,mol.createdat as submitdatecompliance
			,u1.fullname as createdby
			,mom.totalcost as amount
			,mmls.[status_name] as emolstatus
			,mmls.status_desc as statusdescription
			,
			case
				when  coalesce(wft1.[status], wft2.[status]) != 'Complete' then null
				when mol.isactive = 0 then 'Delete'
				when mol.createdby = mol.modifiedby then 'Add'
				when mol.createdby != mol.modifiedby then 'Ok'
			end materialstatus
			,case when coalesce(wft1.[status], wft2.[status]) = 'Complete' then u2.fullname end as approvalname
			,case when coalesce(wft1.[status], wft2.[status]) = 'Complete' then coalesce(wft1.modifiedat, wft2.modifiedat) end as approvaldateutc
			,case when coalesce(wft1.[status], wft2.[status]) = 'Complete' then coalesce(wft1.modifiedat, wft2.modifiedat) end as modifiedutddate
			,coalesce(pmi1.materialquantity, pmi2.materialquantity) as quantityvalidation
			,coalesce(pmi1.batch, pmi2.batch) as batchvalidation
			,coalesce(pmi1.basicstartdate, pmi2.basicstartdate) as eddvalidation
			,case when coalesce(wft1.[status], wft2.[status]) = 'Complete' then coalesce(wft1.modifiedat, wft2.modifiedat) end as validationdate
			,mom.createdat as emolorderdate
			,sso.mono as sapmono
			,sso.poolingstatus as poolingstatus
			,sso.sapstatus as sapstatus
			,sso.saptext as saptext
			,sso.createdutcdate as sapsyncstartdate
			,case when sso.sapstatus = 1 then sso.modifiedutcdate else null end as sapsynccompleteddate
			,moa.mostatus as mostatus
			,
			case
				when moa.approval2date >= moa.approval1date then
					case when moa.approval2date != '00000000' then convert(date, moa.approval2date, 112) else null end
				else
					case when moa.approval1date != '00000000' then convert(date, moa.approval1date, 112) else null end
			end as moapprovaldate
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
		from mechanicorderlist mol
		left join mechanicordersummary mos
		on mol.mechanicordersummaryid = mos.id
		left join mechanicorderdetail mod
		on mol.id = mod.mechanicorderlistid
		left join mechanicordermaterial mom
		on mol.id = mom.mechanicorderlistid
		left join poolingmoitem pmi1
		on mol.number = pmi1.emolnumber and mom.mechanicorderlistid is null
		left join poolingmoitem pmi2
		on mol.number = pmi2.emolnumber and mom.materialnumber = pmi2.materialnumber
		left join sapmosyncorder sso
		on sso.poolingid = coalesce(pmi1.poolingid, pmi2.poolingid)
		left join workflowtransaction wft1
		on mol.workorderid = wft1.referencetransactionid
		left join workflowtransaction wft2
		on mol.mechanicordersummaryid = wft2.referencetransactionid
		left join moapproval moa
		on  concat('00',sso.mono) = moa.monumber
		left join [user] u1
		on mol.createdby = u1.code
		left join [user] u2
		on coalesce(wft1.[status], wft2.[status]) = 'Complete' and coalesce(wft1.modifiedby, wft2.modifiedby) = u2.code
		left join mapping_mol_status mmls
		on mol.[status] = mmls.mol_status
	) a
	where correct_status = 1
),
sap_material_info as
(
	select
		mo.summaryreference
		,mo.mechanicorderdetailid
		,mo.mechanicordermaterialid
		,mo.actionremedycode
		,mo.assetnumber as mo_assetnumber
		,sap.assetnumber as sap_assetnumber
		,case when mo.assetnumber = sap.assetnumber then 1 else 0 end issameequipment
		,mo.materialnumber as mo_materialnumber
		,sap.materialnumber as sap_materialnumber
		,case when mo.materialnumber = sap.materialnumber then 1 else 0 end issamematerialnumber
		,mo.materialranking as mo_materialranking
		,case when mo.materialranking = 'A' then 1 else 0 end ismaterialrankinga
		,case when mo.materialranking = 'B' then 1 else 0 end ismaterialrankingb
		,case when mo.materialranking = 'C' then 1 else 0 end ismaterialrankingc
		,case when mo.materialranking = 'D' then 1 else 0 end ismaterialrankingd
		,case when mo.materialranking = 'E' then 1 else 0 end ismaterialrankinge
		,sap.[status] as sap_mostatus
		,case when sap.[status] = 'CRTD' then 1 else 0 end ismotrackingctrd
		,case when sap.[status] = 'REL' then 1 else 0 end ismotrackingrel
		,case when sap.[status] = 'TECO' then 1 else 0 end ismotrackingteco
		,case when sap.[status] = 'CLSD' then 1 else 0 end ismotrackingclsd
		,mo.quantity as mo_quantity
		,sap.reservationquantity as sap_quantity
		,case when mo.quantity = sap.reservationquantity then 1 else 0 end issamematerialqty
		,sap.grstatus
		,case when lower(sap.grstatus) = 'partial' then 1 else 0 end isgrstatuspartial
		,case when lower(sap.grstatus) = 'full' then 1 else 0 end isgrstatusfull
		,sap.gistatus
		,case when lower(sap.gistatus) = 'partial' then 1 else 0 end isgistatusfull
		,case when lower(sap.gistatus) = 'full' then 1 else 0 end isgistatuspartial
	from
	(
		select distinct
			case when mos.id is null then 0 else 1 end summaryreference
			,coalesce(mos.sitecode, met.sitecode) as sitecode
			,mod.id as mechanicorderdetailid
			,mom.id as mechanicordermaterialid
			,mom.materialnumber
			,mom.quantity
			,mom.materialranking
			,coalesce(mos.assetnumber, met.assetnumber) as assetnumber
			,coalesce(mod.actionremedycode, met.actionremedycode) as actionremedycode
		from mechanicorderlist as mol
		left join mechanicordersummary as mos
		on mol.mechanicordersummaryid = mos.id and mol.status = 'Complete'
		left join mechanicorderdetail as mod
		on mol.id = mod.mechanicorderlistid and mol.status = 'Complete'
		left join mechanicordermaterial as mom
		on mol.id = mom.mechanicorderlistid
		left join
		(
			select distinct
				wo.id as workorderid
				,tpf.id as taskpersonalizedfindingid
				,wo.sitecode
				,wo.assetnumber
				,tpf.actionremedycode
			from workorder wo
			inner join task t
			on wo.id = t.workorderid
			left join taskpersonalized as tp
			on t.id = tp.taskid
			left join taskpersonalizedfinding as tpf
			on tp.id = tpf.taskpersonalizedid
		 ) met
		on mol.workorderid = met.workorderid and mol.taskpersonalizedfindingid = met.taskpersonalizedfindingid and mol.status = 'Complete'
	) mo
	left join
	(
		select
			cpo.assetnumber
			,cpo.materialnumber
			,cpo.monumber
			,cpo.status
			,cpo.reservationquantity
			,cpo.grstatus
			,cpo.gistatus
			,cpo.gidate
			,cpo.modescription
			,m.ranking
		from checkpartorder cpo
		inner join sapmosyncorder sso
		on cpo.monumber = sso.mono and sso.poolingstatus not in ('MOJ','MOK')
		left join material m
		on cpo.materialnumber = m.number and cpo.sitecode = m.siteid
	) sap
	on mo.materialnumber = sap.materialnumber and mo.assetnumber = sap.assetnumber
),
pooling_validation_result as
(
	select distinct
		smi.summaryreference
		,smi.mechanicorderdetailid
		,smi.mechanicordermaterialid
		,mpv.id
		,mpv.colorcategory
		,
		case
			when smi.actionremedycode = 'AR0010' and smi.mechanicordermaterialid is null then 1
			else mpv.canactiondigimandelete
		 end as canactiondigimandelete
		,mpv.canactionsappushdelete
		,mpv.cancreatemo
		,mpv.cancreatemowithnote
		,mpv.remark
	from sap_material_info smi
	inner join mapping_pooling_validation mpv
	on 1 = 1
	and smi.issameequipment = mpv.issameequipment
	and smi.issamematerialnumber = mpv.issamematerialnumber
	and
	(
		smi.ismaterialrankinga = mpv.ismaterialrankinga
		or smi.ismaterialrankingb = mpv.ismaterialrankingb
		or smi.ismaterialrankingc = mpv.ismaterialrankingc
		or smi.mo_materialranking is null
		or smi.mo_materialranking = ''
	)
	and
	(
		smi.ismaterialrankingd = mpv.ismaterialrankingd
		or smi.ismaterialrankinge = mpv.ismaterialrankinge
	)
	and
	(
		smi.ismotrackingctrd = mpv.ismotrackingctrd
		or smi.ismotrackingrel = mpv.ismotrackingrel
	)
	and
	(
		smi.ismotrackingteco = mpv.ismotrackingteco
		or smi.ismotrackingclsd = mpv.ismotrackingclsd
	)
	and smi.issamematerialqty = mpv.issamematerialqty
	and smi.isgrstatuspartial = mpv.isgrstatuspartial
	and smi.isgrstatusfull = mpv.isgrstatusfull
	and smi.isgistatuspartial = mpv.isgistatuspartial
	and smi.isgistatusfull = mpv.isgistatusfull
),
base_form as
(
	select distinct
		mot.summaryreference
		,mot.workorderid
		,mot.taskpersonalizedfindingid
		,mot.mechanicorderdetailid
		,mot.mechanicordermaterialid
		,mot.date_id
		,coalesce(mot.mono, met.mono) as mono
		,coalesce(mot.inspectiontype, met.inspectiontype) as inspectiontype
		,coalesce(mot.assetnumber, met.assetnumber) as assetnumber
		,coalesce(mot.usercode, met.usercode) as usercode
		,coalesce(mot.componentcode, met.componentcode) as componentcode
		,coalesce(mot.subcomponentcode, met.subcomponentcode) as subcomponentcode
		,coalesce(mot.othersubcomponentname, met.othersubcomponentname) as othersubcomponentname
		,coalesce(mot.actionremedycode, met.actionremedycode) as actionremedycode
		,coalesce(mot.prioritycode, met.prioritycode) as prioritycode
		,coalesce(mot.damagecode, met.damagecode) as damagecode
		,coalesce(mot.sectiontypecode, met.sectiontypecode) as sectiontypecode
		,coalesce(mot.sitecode, met.sitecode) as sitecode
		,mot.submittedutcdateutc
		,mot.submittedutcdate
		,mot.aging
		,mot.emolno
		,mot.detailid
		,mot.eddmol
		,mot.motype
		,mot.deletereason
		,mot.materialnumber
		,mot.materialdescription
		,mot.quantity
		,mot.unit
		,mot.materialranking
		,mot.batch
		,mot.submitdate
		,mot.submitdatecompliance
		,mot.createdby
		,mot.amount
		,mot.emolstatus
		,mot.statusdescription
		,mot.materialstatus
		,mot.approvalname
		,mot.approvaldateutc
		,mot.modifiedutddate
		,mot.quantityvalidation
		,mot.batchvalidation
		,mot.eddvalidation
		,mot.validationdate
		,mot.emolorderdate
		,mot.sapmono
		,mot.poolingstatus
		,mot.sapstatus
		,mot.saptext
		,mot.sapsyncstartdate
		,mot.sapsynccompleteddate
		,mot.mostatus
		,mot.moapprovaldate
	from maintenance_order_transformation mot
	left join maintenance_execution_transformation met
	on met.workorderid = mot.workorderid and met.taskpersonalizedfindingid = mot.taskpersonalizedfindingid and mot.summaryreference = 0
)


select
	cast([Date_Id] as varchar(10)) [Date_Id]
	,cast([MONo] as varchar(25)) [MONo]
	,cast([InspectionType] as varchar(12)) [InspectionType]
	,cast([UnitCode] as varchar(25)) [UnitCode]
	,cast([ModelName] as varchar(25)) [ModelName]
	,cast([SubmittedUtcDateUTC] as datetime) [SubmittedUtcDateUTC]
	,cast([SubmittedUtcDate] as datetime) [SubmittedUtcDate]
	,cast([Aging] as int) [Aging]
	,cast([InspectorName] as varchar(255)) [InspectorName]
	,cast([EMOLNo] as varchar(50)) [EMOLNo]
	,cast([DetailId] as varchar(50)) [DetailId]
	,cast([InspectDescription] as nvarchar(2053)) [InspectDescription]
	,cast([ComponentName] as varchar(512)) [ComponentName]
	,cast([SubComponentId] as varchar(50)) [SubComponentId]
	,cast([SubComponentName] as varchar(512)) [SubComponentName]
	,cast([ActionName] as varchar(512)) [ActionName]
	,cast([PriorityName] as varchar(512)) [PriorityName]
	,cast([EDDMOL] as datetime) [EDDMOL]
	,cast([MOType] as varchar(10)) [MOType]
	,cast([DeleteReason] as varchar(512)) [DeleteReason]
	,cast([MaterialNumber] as varchar(4000)) [MaterialNumber]
	,cast([MaterialDescription] as varchar(4000)) [MaterialDescription]
	,cast([Quantity] as decimal(18,2)) [Quantity]
	,cast([Unit] as varchar(4000)) [Unit]
	,cast([MaterialRanking] as varchar(4000)) [MaterialRanking]
	,cast([Batch] as varchar(4000)) [Batch]
	,cast([SubmitDate] as datetime) [SubmitDate]
	,cast([SubmitDateCompliance] as datetime) [SubmitDateCompliance]
	,cast([CreatedBy] as varchar(4000)) [CreatedBy]
	,cast([Amount] as decimal(18,2)) [Amount]
	,cast([DamageCodeName] as varchar(512)) [DamageCodeName]
	,cast([EMOLStatus] as varchar(16)) [EMOLStatus]
	,cast([StatusDescription] as varchar(35)) [StatusDescription]
	,cast([MaterialStatus] as varchar(6)) [MaterialStatus]
	,cast([ApprovalName] as varchar(4000)) [ApprovalName]
	,cast([ApprovalDateUTC] as datetime) [ApprovalDateUTC]
	,cast([ModifiedUtdDate] as datetime) [ModifiedUtdDate]
	,cast([QuantityValidation] as varchar(50)) [QuantityValidation]
	,cast([BatchValidation] as varchar(20)) [BatchValidation]
	,cast([EDDValidation] as datetime) [EDDValidation]
	,cast([Category] as varchar(100)) [Category]
	,cast([Remark] as varchar(500)) [Remark]
	,cast([Notes] as varchar(1024)) [Notes]
	,cast([Activity] as varchar(100)) [Activity]
	,cast([ValidationBy] as varchar(4000)) [ValidationBy]
	,cast([ValidationDate] as datetime) [ValidationDate]
	,cast([Section] as varchar(512)) [Section]
	,cast([SiteId] as varchar(12)) [SiteId]
	,cast([SiteName] as varchar(255)) [SiteName]
	,cast([eMOLOrderDate] as varchar(10)) [eMOLOrderDate]
	,cast([SAPMONo] as varchar(32)) [SAPMONo]
	,cast([PoolingStatus] as varchar(6)) [PoolingStatus]
	,cast([SAPStatus] as int) [SAPStatus]
	,cast([SAPText] as varchar(1024)) [SAPText]
	,cast([SAPSyncStartDate] as datetime) [SAPSyncStartDate]
	,cast([SAPSyncCompletedDate] as datetime) [SAPSyncCompletedDate]
	,cast([MOStatus] as varchar(50)) [MOStatus]
	,cast([MOApprovalDate] as date) [MOApprovalDate]
from
(
	select distinct
		bf.date_id as Date_Id
		,bf.mono as MONo
		,bf.inspectiontype as InspectionType
		,bf.assetnumber as  UnitCode
		,am.[name] as ModelName
		,dateadd(hour, s.utcoffset, bf.submittedutcdateutc) as SubmittedUtcDateUTC
		,bf.submittedutcdate as SubmittedUtcDate
		,bf.aging as Aging
		,u.fullname as InspectorName
		,bf.emolno as EMOLNo
		,bf.detailid as DetailId
		,concat(c.[name], ' ', case when isnull(bf.subcomponentcode, '') = '' then bf.othersubcomponentname else sc.[name] end, ' ', dc.[name], ' (', dg.[name], ')') as InspectDescription
		,c.[name] as ComponentName
		,bf.componentcode as SubComponentId
		,case when isnull(bf.subcomponentcode, '') = '' then concat('Others; ', bf.othersubcomponentname) else sc.[name] end as SubComponentName
		,ar.[name] as ActionName
		,concat(p.code, ' - ',	p.[description]) as PriorityName
		,bf.eddmol as EDDMOL
		,bf.motype as MOType
		,bf.deletereason as DeleteReason
		,bf.materialnumber as MaterialNumber
		,bf.materialdescription as MaterialDescription
		,bf.quantity as Quantity
		,bf.unit as Unit
		,bf.materialranking as MaterialRanking
		,bf.batch as Batch
		,dateadd(hour, s.utcoffset, bf.submitdate) as SubmitDate
		,dateadd(hour, s.utcoffset, bf.submitdatecompliance) as SubmitDateCompliance
		,bf.createdby as CreatedBy
		,bf.amount as Amount
		,dc.[name] as DamageCodeName
		,bf.emolstatus as EMOLStatus
		,bf.statusdescription as StatusDescription
		,bf.materialstatus as MaterialStatus
		,bf.approvalname as ApprovalName
		,dateadd(hour, s.utcoffset, bf.approvaldateutc) as ApprovalDateUTC
		,bf.modifiedutddate as ModifiedUtdDate
		,bf.quantityvalidation as QuantityValidation
		,bf.batchvalidation as BatchValidation
		,bf.eddvalidation as EDDValidation
		,coalesce(pvr1.colorcategory, pvr2.colorcategory) as Category
		,coalesce(pvr1.remark, pvr2.remark) as Remark
		,null as Notes
		,case when bf.sapstatus = 1 then 'CreateSAP' else null end as Activity
		,bf.approvalname as ValidationBy
		,bf.validationdate as ValidationDate
		,st.[name] as Section
		,bf.sitecode as SiteId
		,s.[name] as SiteName
		,dateadd(hour, s.utcoffset, bf.emolorderdate) as eMOLOrderDate
		,bf.sapmono as SAPMONo
		,bf.poolingstatus as PoolingStatus
		,bf.sapstatus as SAPStatus
		,bf.saptext as SAPText
		,dateadd(hour, s.utcoffset, bf.sapsyncstartdate) as SAPSyncStartDate
		,dateadd(hour, s.utcoffset, bf.sapsynccompleteddate) as SAPSyncCompletedDate
		,bf.mostatus as MOStatus
		,bf.moapprovaldate as MOApprovalDate
	from base_form bf
	left join sectiontype st
	on bf.sectiontypecode = st.code
	left join [site] s
	on bf.sitecode = s.code
	left join asset a
	on bf.assetnumber = a.assetnumber
	left join assetmodel am
	on a.assetmodelcode = am.code
	left join component c
	on bf.componentcode = c.code
	left join subcomponent sc
	on bf.subcomponentcode = sc.code
	left join actionremedy ar
	on bf.actionremedycode = ar.code
	left join [priority] p
	on bf.prioritycode = p.code and p.[group] = 'Inspection'
	left join damagecode dc
	on bf.damagecode = dc.code
	left join damagegroup dg
	on dc.damagegroupcode = dg.code
	left join [user] u
	on bf.usercode = u.code
	left join pooling_validation_result pvr1
	on bf.mechanicordermaterialid = pvr1.mechanicordermaterialid and bf.summaryreference = pvr1.summaryreference
	left join pooling_validation_result pvr2
	on bf.mechanicorderdetailid = pvr2.mechanicorderdetailid and bf.summaryreference = pvr2.summaryreference
) a
GO
