
BEGIN
    SET NOCOUNT ON;

    -- =============================================
    -- Declare Parameters
    -- =============================================
    DECLARE @mandt VARCHAR(3) = '300';
    DECLARE @werks VARCHAR(4) = '2009';

    -- =============================================
    -- Temp Table #temp_zmchb
    -- =============================================
    DROP TABLE IF EXISTS #temp_zmchb;

    SELECT TOP 1 WITH TIES
        matnr,
        werks,
        lgort,
        charg,
        ISNULL(clabs, 0) AS clabs
    INTO #temp_zmchb
    FROM [HANA].HANA.zmchb
    WHERE mandt = @mandt
      AND werks = @werks
      AND lgort LIKE '%WH0%'
      AND lgort NOT IN ('3PL1', '3PL2', 'HO01')
    ORDER BY ROW_NUMBER() OVER (
        PARTITION BY werks, matnr
        ORDER BY lgort
    );

    -- =============================================
    -- Temp Table #temp_zmard
    -- =============================================
    DROP TABLE IF EXISTS #temp_zmard;

    SELECT TOP 1 WITH TIES
        matnr,
        werks,
        lgort,
        ISNULL(labst, 0) AS labst
    INTO #temp_zmard
    FROM [HANA].HANA.zmard
    WHERE mandt = @mandt
      AND werks = @werks
      AND lgort LIKE '%WH0%'
      AND lgort NOT IN ('3PL1', '3PL2', 'HO01')
    ORDER BY ROW_NUMBER() OVER (
        PARTITION BY werks, matnr
        ORDER BY lgort
    );

    -- =============================================
    -- Temp Table #temp_table - Final Join
    -- =============================================
    DROP TABLE IF EXISTS #temp_table;

    SELECT
        TRIM(REPLACE(REPLACE(a.objek, N'?', '-'), N' ', '-')) AS MATNR,
        e.bwkey AS BWKEY,
        CASE
            WHEN e.bwtty <> '' THEN i.lgort
            ELSE j.lgort
        END AS LGORT,
        e.bwtar AS BWTAR,
        f.mstae AS MSTAE,
        TRIM(REPLACE(REPLACE(ISNULL(g.maktx, ''), N'?', '-'), N' ', '-')) AS MAKTX,
        e.verpr AS VERPR,
        e.verpr *
        (
            SELECT TOP 1
                CAST(ukurs * 1000 AS NUMERIC(11, 0))
            FROM [HANA].HANA.tcurr
            WHERE kurst = 'ZR'
              AND fcurr = 'USD'
              AND tcurr = 'IDR'
              AND mandt = '300'
            ORDER BY gdatu ASC
        ) AS VERPR_2,
        CASE
            WHEN e.bwtty <> '' THEN i.clabs
            ELSE j.labst
        END AS STOCK,
        f.meins AS MEINS,
        h.maabc AS RANKING,
        (
            SELECT x.atwrt
            FROM [HANA].HANA.ausp x
            INNER JOIN [HANA].HANA.cabn y
                ON y.atinn = x.atinn
               AND y.atnam = 'EQP_MOD_HIR'
               AND y.mandt = x.mandt
            WHERE x.objek = a.objek
              AND x.mandt = a.mandt
        ) AS ATWRT,
        a.atwrt AS ATWRT_2,
        CASE
            WHEN f.mstae IN ('Z1','04') THEN 0
            ELSE 1
        END AS IsActive
    INTO #temp_table
    FROM [HANA].HANA.ausp a
    INNER JOIN [HANA].HANA.cabn c
        ON c.atinn = a.atinn
       AND c.atnam LIKE 'MODEL_UNIT%'
       AND c.mandt = @mandt
    INNER JOIN [HANA].HANA.mbew e
        ON e.matnr = a.objek
       AND e.mandt = a.mandt
       AND e.bwkey = @werks
       AND e.bwtar IN ('NEW', 'REPAIRED', '')
    INNER JOIN [HANA].HANA.mara f
        ON f.matnr = e.matnr
       AND f.mandt = @mandt
    LEFT JOIN [HANA].HANA.makt g
        ON g.matnr = a.objek
       AND g.mandt = @mandt
       AND g.spras = 'E'
    LEFT JOIN [HANA].HANA.marc h
        ON h.matnr = e.matnr
       AND h.mandt = @mandt
       AND h.werks = @werks
    LEFT JOIN #temp_zmchb i
        ON i.matnr = e.matnr
       AND i.werks = @werks
    LEFT JOIN #temp_zmard j
        ON j.matnr = e.matnr
       AND j.werks = @werks
    WHERE a.mandt = @mandt
      AND a.klart = '001';

    -- =============================================
    -- Temp Final with ROW_NUMBER
    -- =============================================
    DROP TABLE IF EXISTS #temp_final;

    SELECT
        MATNR,
        BWKEY,
        LGORT,
        BWTAR,
        MSTAE,
        MAKTX,
        VERPR,
        VERPR_2,
        STOCK,
        MEINS,
        RANKING,
        ATWRT,
        ATWRT_2,
        IsActive
    INTO #temp_final
    FROM
    (
        SELECT
            ROW_NUMBER() OVER (
                PARTITION BY BWKEY, MATNR, BWTAR, ATWRT_2
                ORDER BY STOCK
            ) AS RowNum,
            *
        FROM #temp_table
    ) X
    WHERE RowNum = 1;

    CREATE INDEX IX_temp_final_keys
        ON #temp_final (MATNR, BWKEY, BWTAR, ATWRT_2);

 UPDATE tf
 SET tf.ATWRT = eq.Equipment_Hierarchy
 FROM #temp_final tf
 INNER JOIN (
  SELECT DISTINCT Equipment_Hierarchy, Model_Unit
  FROM [DM_DIM].[dbo].[DIM_EQUIPMENT]
 ) eq
 ON tf.ATWRT_2 = eq.Model_Unit;
 
 DELETE FROM #temp_final WHERE ATWRT = 'HEAVY WATER TRUCK';
 
    -- =============================================
    -- Update Existing Data
    -- =============================================
    UPDATE Tgt
    SET
        Tgt.LGORT = Src.LGORT,
        Tgt.MSTAE = Src.MSTAE,
        Tgt.MAKTX = Src.MAKTX,
        Tgt.VERPR = Src.VERPR,
        Tgt.VERPR_2 = Src.VERPR_2,
        Tgt.STOCK = Src.STOCK,
        Tgt.MEINS = Src.MEINS,
        Tgt.RANKING = Src.RANKING,
        Tgt.IsActive = Src.IsActive,
        Tgt.LastUpdatedUtcDate = GETUTCDATE()
    FROM [md_plt].[material_2009] Tgt
    INNER JOIN #temp_final Src
        ON Tgt.MATNR = Src.MATNR
       AND Tgt.BWKEY = Src.BWKEY
       AND Tgt.BWTAR = Src.BWTAR
       AND Tgt.ATWRT_2 = Src.ATWRT_2
    CROSS APPLY
    (
        SELECT
            hash_m = CHECKSUM(
                ISNULL(CONVERT(VARCHAR(255), Tgt.MAKTX), ''),
                ISNULL(CONVERT(FLOAT, Tgt.VERPR), 0),
                ISNULL(CONVERT(VARCHAR(200), Tgt.LGORT), ''),
                ISNULL(CONVERT(INT, Tgt.STOCK), 0),
                ISNULL(CONVERT(VARCHAR(25), Tgt.RANKING), '')
            ),
            hash_s = CHECKSUM(
                ISNULL(CONVERT(VARCHAR(255), Src.MAKTX), ''),
                ISNULL(CONVERT(FLOAT, Src.VERPR), 0),
                ISNULL(CONVERT(VARCHAR(200), Src.LGORT), ''),
                ISNULL(CONVERT(INT, Src.STOCK), 0),
                ISNULL(CONVERT(VARCHAR(25), Src.RANKING), '')
            )
    ) h
    WHERE Tgt.BWKEY = @werks
      AND h.hash_m <> h.hash_s;

    -- =============================================
    -- Insert New Records
    -- =============================================
    INSERT INTO [md_plt].[material_2009]
    (
        MATNR,
        BWKEY,
        LGORT,
        BWTAR,
        MSTAE,
        MAKTX,
        VERPR,
        VERPR_2,
        STOCK,
        MEINS,
        RANKING,
        ATWRT,
        ATWRT_2,
        IsActive
    )
    SELECT
        S.MATNR,
        S.BWKEY,
        S.LGORT,
        S.BWTAR,
        S.MSTAE,
        S.MAKTX,
        S.VERPR,
        S.VERPR_2,
        S.STOCK,
        S.MEINS,
        S.RANKING,
        S.ATWRT,
        S.ATWRT_2,
        S.IsActive
    FROM #temp_final S
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM md_plt.material_2009 T
        WHERE T.MATNR = S.MATNR
          AND T.BWKEY = S.BWKEY
          AND T.BWTAR = S.BWTAR
          AND T.ATWRT_2 = S.ATWRT_2
    );
END;