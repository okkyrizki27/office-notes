CREATE   view [dbo].[vw_dim_equipment]
as
select * from 
(
	select distinct
	site_id, equipment_id, equipment, b.modelid model_unit_id, model_unit, equipment_category_desc,
	equipment_class, manufacturer, b.sectiontypecode sub_section_type_code, d.sectiontypename sub_section_type_code_name,
	a.section_type_code, c.sectiontypename section_type_code_name, e.statusunit status_unit
	from 
	(
		select siteid site_id, id equipment_id, equipmentname equipment, modelunit model_unit, equipmentcategory equipment_category, equipmentcategorydesc equipment_category_desc,
		equipmentclass equipment_class, manufacturer, sectiontypecode section_type_code
		from [app_wicope].[dbo].[equipment] a 
		where isactive = 1
	) a
	left join [app_wicope].[dbo].[equipmentmodel] b
	on a.model_unit = b.modelname and b.isactive = 1
	left join  [app_wicope].[dbo].[sectiontype] c
	on a.section_type_code = c.sectiontypecode
	left join  [app_wicope].[dbo].[sectiontype] d
	on b.sectiontypecode = d.sectiontypecode
	left join (
		select top 1 with ties equipmentname, statusunit from [app_wicope].[dbo].[unitstatus]
		order by row_number() over(partition by equipmentname order by [createdutcdate] desc)
	) e
	on a.equipment = e.equipmentname
) a
where section_type_code_name is not null and section_type_code_name not in ('OTHERS', 'LIGHTING TOWER') and status_unit = 'INPR'
GO