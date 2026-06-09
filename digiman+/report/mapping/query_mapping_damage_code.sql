-- =============================================
-- Description : Query mapping damage code
--               Model > Component > Sub Component > Damage Code
-- =============================================

SELECT
      b.AssetModelCode
      ,c.Name as [Model]
      ,a.[ComponentCode]
      ,d.Name as [Component]
      ,a.[SubComponentCode]
      ,e.Name [SubComponent]
      ,g.Name as [DamageCode]
      ,a.[IsActive]
      ,a.[CreatedAt]
      ,a.[CreatedBy]
      ,a.[ModifiedAt]
      ,a.[ModifiedBy]
  FROM [dbo].[ModelComponentSubComponent] a
  LEFT JOIN [dbo].[AssetModelMapping] b ON a.AssetModelMappingCode=b.Code
  LEFT JOIN [dbo].[AssetModel] c ON b.AssetModelCode=c.Code
  LEFT JOIN [dbo].[Component] d ON a.ComponentCode=d.Code
  LEFT JOIN [dbo].[SubComponent] e ON a.SubComponentCode=e.Code
  LEFT JOIN [dbo].[SubComponentDamage] f ON a.SubComponentCode=f.SubComponentCode
  LEFT JOIN [dbo].[DamageCode] g ON f.DamageCode=g.Code
  ORDER BY SubComponentCode ASC
