CREATE OR ALTER PROCEDURE [am].[usp_tr_am_material]
 @siteid varchar(25)
AS
BEGIN

 DECLARE @sql NVARCHAR(MAX)
 DECLARE @date VARCHAR(8)

 SET @date = CONVERT(VARCHAR(8), DATEADD(HH, 7 , GETUTCDATE()), 112)

 SET @sql = N'
   WITH StageCTE AS (
    SELECT
     ROW_NUMBER() OVER(
      PARTITION BY
       MATNR,
       MAKTX,
       BWTAR,
       rca.SectionTypeCode,
       BWKEY
      ORDER BY STOCK DESC
     ) AS RowNumb,
     MAKTX AS [Description],
     MATNR AS [Number],
     RANKING AS [Ranking],
     MEINS AS [UoMCode],
     BWTAR AS [BatchCode],
     STOCK AS [Stock],
     VERPR AS [MAP],
     VERPR_2 AS [MAPLocalCurr],
     BWKEY AS [SiteId],
     rca.AssetModelCode,
     rca.SectionTypeCode AS SectionTypeCode,
     LGORT AS StorageLocation,
     rm.IsActive
    FROM OPENROWSET(
     BULK ''assetmanagement/buma/material/' + @date + '/material' + @siteid + '.parquet'',
     DATA_SOURCE = ''raw_dfs_core_windows_net'',
     FORMAT = ''parquet''
    ) WITH (
     MAKTX varchar(50),
     MATNR varchar(50),
     RANKING varchar(50),
     MEINS varchar(50),
     BWTAR varchar(50),
     STOCK varchar(50),
     VERPR varchar(50),
     VERPR_2 varchar(50),
     BWKEY varchar(50),
     LGORT varchar(50),
     ATWRT_2 varchar(100),
     IsActive bit
    ) AS rm
    INNER JOIN (
     SELECT
      client.AssetModelCode,
      client.SectionTypeCode,
      asset.[Name]
     FROM OPENROWSET(
      BULK ''assetmanagement/buma/clientassetmapping/*.parquet'',
      DATA_SOURCE = ''raw_dfs_core_windows_net'',
      FORMAT = ''parquet''
     ) WITH (
      AssetModelCode varchar(50),
      SectionTypeCode varchar(25),
      IsActive bit
     ) AS client
     INNER JOIN (
      SELECT
       Code,
       [Name],
       IsActive
      FROM OPENROWSET(
       BULK ''assetmanagement/buma/assetmodel/*.parquet'',
       DATA_SOURCE = ''raw_dfs_core_windows_net'',
       FORMAT = ''parquet''
      ) WITH (
       Code varchar(50),
       [Name] varchar(80),
       IsActive bit
      ) AS assetmodel
     ) AS asset
      ON client.AssetModelCode = asset.Code
     WHERE
      client.IsActive = 1
      AND asset.IsActive = 1
    ) AS rca
     ON rm.ATWRT_2 = rca.[Name]
    WHERE ISNULL(RANKING,'''') != ''''
  )
  SELECT
   [Description],
   [Number],
   [Ranking],
   [UoMCode],
   [BatchCode],
   [Stock],
   [MAP],
   [MAPLocalCurr],
   [SiteId],
   [AssetModelCode],
   [SectionTypeCode],
   [StorageLocation],
   [IsActive]
  FROM StageCTE WHERE RowNumb = 1'

 print(@sql)
 EXEC sp_executesql @sql
END