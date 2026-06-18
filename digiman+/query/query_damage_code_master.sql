-- =============================================
-- Description : Query damage code master
--               Damage Group > Damage Code
-- =============================================

SELECT
      a.[DamageGroupCode]
      ,b.Name [GroupName]
      ,a.[Code] as [DamageCode]
      ,a.[Name] as Damage
      ,a.[Description]
      ,a.[IsActive]
      ,a.[CreatedAt]
      ,a.[CreatedBy]
      ,a.[ModifiedAt]
      ,a.[ModifiedBy]
  FROM [dbo].[DamageCode] a
  LEFT JOIN [dbo].[DamageGroup] b ON a.DamageGroupCode=b.Code
