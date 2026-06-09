-- =============================================
-- Description : Get data equipment by site
-- =============================================


-- Query 1: Get equipment by asset number list
SELECT TOP (1000)
       [Id]
      ,[BlobPath]
      ,[AssetNumber]
      ,[SiteCode]
      ,[AssetTypeCode]
      ,[AssetClassCode]
      ,[AssetVariantCode]
      ,[AssetModelCode]
      ,[BrandCode]
      ,[AssetCategoryCode]
      ,[SectionTypeCode]
      ,[AssetOwnershipCode]
      ,[UoMCode]
      ,[TargetLife]
      ,[AssetSerialNumber]
      ,[AssetDealer]
      ,[Status]
      ,[IsActive]
      ,[CreatedAt]
      ,[CreatedBy]
      ,[ModifiedAt]
      ,[ModifiedBy]
  FROM [dbo].[Asset]
  WHERE AssetNumber

--  IN (
--    'HDRT77001',
--    'HDRT77002',
--    'HDRT77003',
--    'HDRT77004',
--    'HDRT77005',
--    'HDRT77006',
--    'HDRT77007',
--    'HDRT77008',
--    'HDRT77009',
--    'HDRT77010',
--    'HDRT77011',
--    'HDRT77012',
--    'HDRT78001',
--    'HDRT78002',
--    'HDRT78003',
--    'HDRT78004',
--    'HDRT78005',
--    'HDRT78006',
--    'HDRT78007',
--    'HDRT78008',
--    'HDRT78009',
--    'HDRT78010',
--    'HDRT78011'
--  )

  IN (
    'EXHC25008',
    'EXHC25011',
    'HDCT77010',
    'HDCT77019',
    'HDCT77063',
    'HDCT77337',
    'HDCT77207',
    'HDCT77219',
    'HDCT77223',
    'HDCT77231',
    'HDCT77249',
    'HDCT77250',
    'HDCT77251',
    'HDCT77260',
    'HDCT77265',
    'HDCT77301',
    'HDCT77315',
    'HDCT77339',
    'HDCT77345',
    'HDCT77388',
    'HDCT77401',
    'HDKM78321',
    'BDKM37040'
  )


-- =============================================
-- Query 2: Get equipment by site with model & brand
-- =============================================

SELECT
       a.[Id]
      ,a.[BlobPath]
      ,a.[AssetNumber]
      ,a.[SiteCode]
      ,a.[AssetTypeCode]
      ,a.[AssetClassCode]
      ,a.[AssetVariantCode]
      ,a.[AssetModelCode]
      ,b.Name AS [ModelName]
      ,a.[BrandCode]
      ,c.Name AS [Brand]
      ,a.[AssetCategoryCode]
      ,a.[SectionTypeCode]
      ,a.[AssetOwnershipCode]
      ,a.[UoMCode]
      ,a.[TargetLife]
      ,a.[AssetSerialNumber]
      ,a.[AssetDealer]
      ,a.[Status]
      ,a.[IsActive]
      ,a.[CreatedAt]
      ,a.[CreatedBy]
      ,a.[ModifiedAt]
      ,a.[ModifiedBy]
  FROM [dbo].[Asset] a
  LEFT JOIN [dbo].[AssetModel] b ON a.AssetModelCode = b.Code
  LEFT JOIN [dbo].[AssetBrand] c ON a.BrandCode = c.Code
  WHERE SiteCode = 2010
  AND AssetCategoryCode IN ('A', 'C')
  -- AND SectionTypeCode IS NOT NULL OR SectionTypeCode != ''
