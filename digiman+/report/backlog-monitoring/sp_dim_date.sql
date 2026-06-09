
CREATE PROCEDURE [dbo].[sp_dim_date]
AS

BEGIN

	SET NOCOUNT ON;

	SET DATEFIRST 5;

	DECLARE @CurrentDate DATE = '2019-01-01'
	DECLARE @EndDate DATE = '2035-12-31' --eomonth(CAST(DATEADD(MONTH, +3, GETDATE())  AS DATE))

	drop table if exists #temp_dim_date
	create table #temp_dim_date(
		[date_id] [date] null,
		[date_desc] [varchar](255) null,
		[week_id] [int] null,
		[week_desc] [varchar](255) null,
		[weekreset_desc] [varchar](10) null,
		[weekreset_month_id] [int] null,
		[month_id] [int] null,
		[month_desc] [varchar](255) null,
		[mon_desc] [varchar](255) null,
		[quarter_id] [int] null,
		[quarter_desc] [varchar](255) null,
		[semester_id] [int] null,
		[semester_desc] [varchar](255) null,
		[year] [int] null,
		[day_of_month] [int] null,
		[day_of_week] [int] null,
		[day_of_year] [int] null,
		[previous_day] [date] null,
		[same_day_last_year] [date] null,
		[day_name] [varchar](255) null
	)

	WHILE @CurrentDate <= @EndDate
	BEGIN
			
		INSERT INTO #temp_dim_date (
		   		[date_id],
				[date_desc],
				[week_id],
				[week_desc],
				[month_id],
				[month_desc],
				[mon_desc],
				[quarter_id],
				[quarter_desc],
				[semester_id],
				[semester_desc],
				[year],
				[day_of_month],
				[day_of_week],
				[day_of_year],
				[previous_day],
				[same_day_last_year],
				[day_name]
		)
		SELECT 
			date_id = @CurrentDate,
			date_desc = CONVERT(VARCHAR,@CurrentDate,106),
			week_id = 
				concat(				
					CASE WHEN DATENAME(dy, @CurrentDate) = 1 THEN DATEPART(YEAR,DATEADD(year,-1, @CurrentDate)) ELSE DATEPART(YEAR,@CurrentDate) END,
					CASE WHEN LEN(DATEPART(WEEK,DATEADD(DAY, -1, @CurrentDate))) <= 1 THEN CONCAT('0',DATEPART(WEEK,DATEADD(DAY, -1, @CurrentDate))) ELSE CONVERT(VARCHAR,DATEPART(WEEK,DATEADD(DAY, -1, @CurrentDate))) END
				),
			  
			--CONCAT(DATEPART(YEAR,@CurrentDate),CASE WHEN LEN(DATEPART(WEEK,DATEADD(DAY, -1, @CurrentDate))) <= 1 THEN CONCAT('0',DATEPART(WEEK,DATEADD(DAY, -1, @CurrentDate))) ELSE CONVERT(VARCHAR,DATEPART(WEEK,DATEADD(DAY, -1, @CurrentDate))) END),
			week_desc = CASE WHEN DATENAME(dw, @CurrentDate) = 'Saturday' 
							THEN CONCAT(CONVERT(VARCHAR,CONVERT(VARCHAR,@CurrentDate)),' - ',CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,6,@CurrentDate))))
						WHEN DATENAME(dw, @CurrentDate) = 'Sunday'
							THEN CONCAT(CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,-1,@CurrentDate))),' - ',CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,5,@CurrentDate))))
						WHEN DATENAME(dw, @CurrentDate) = 'Monday'
							THEN CONCAT(CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,-2,@CurrentDate))),' - ',CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,4,@CurrentDate))))
						WHEN DATENAME(dw, @CurrentDate) = 'Tuesday'
							THEN CONCAT(CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,-3,@CurrentDate))),' - ',CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,3,@CurrentDate))))
						WHEN DATENAME(dw, @CurrentDate) = 'Wednesday'
							THEN CONCAT(CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,-4,@CurrentDate))),' - ',CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,2,@CurrentDate))))
						WHEN DATENAME(dw, @CurrentDate) = 'Thursday'
							THEN CONCAT(CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,-5,@CurrentDate))),' - ',CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,1,@CurrentDate))))
						WHEN DATENAME(dw, @CurrentDate) = 'Friday'
							THEN CONCAT(CONVERT(VARCHAR,CONVERT(DATE,DATEADD(dd,-6,@CurrentDate))),' - ',CONVERT(VARCHAR,@CurrentDate))
						END,
			--week_of_month = CONCAT('W', datediff(week, dateadd(week, datediff(day,0,dateadd(month, datediff(month,0,cast(@CurrentDate as datetime)),0))/7, 0),cast(@CurrentDate as datetime)-1) + 1,
			--CHAR(13),CONVERT(VARCHAR(3),CAST(@CurrentDate AS DATETIME),107)),
			month_id = CONCAT(DATEPART(YEAR,@CurrentDate),CASE WHEN LEN(DATEPART(MONTH,@CurrentDate)) <= 1 THEN CONCAT('0',DATEPART(MONTH,@CurrentDate)) ELSE CONVERT(VARCHAR,DATEPART(MONTH,@CurrentDate)) END),
			month_desc = DATENAME(MONTH,@CurrentDate) + CHAR(13) + CONVERT(VARCHAR,DATEPART(YEAR,@CurrentDate)),
			mon_desc = CONVERT(VARCHAR(3),CAST(@CurrentDate AS DATETIME),107) + CHAR(13) + CONVERT(VARCHAR,DATEPART(YEAR,@CurrentDate)),
			quarter_id = CONCAT(DATEPART(YEAR,@CurrentDate),CASE WHEN LEN(DATEPART(QQ,@CurrentDate)) <= 1 THEN CONCAT('0',DATEPART(QQ,@CurrentDate)) ELSE CONVERT(VARCHAR,DATEPART(QQ,@CurrentDate)) END),
			quarter_desc = CONCAT('Quarter', CONVERT(VARCHAR,DATEPART(QQ,@CurrentDate)),CHAR(13),CONVERT(VARCHAR,DATEPART(YEAR,@CurrentDate))),
			semester_id = CASE WHEN DATEPART(QQ,@CurrentDate) <= 2 THEN CONCAT(CONVERT(VARCHAR,DATEPART(YEAR,@CurrentDate)),'01') ELSE CONCAT(CONVERT(VARCHAR,DATEPART(YEAR,@CurrentDate)),'02') END,
			semester_desc = CONCAT('Semester',CHAR(13),CASE WHEN DATEPART(QQ,@CurrentDate) <= 2 THEN '01' ELSE '02' END,CHAR(13) + CONVERT(VARCHAR,DATEPART(YEAR,@CurrentDate))),
			[year] = YEAR(@CurrentDate),
			day_of_month = DAY(@CurrentDate),
			day_of_week = DATEPART(dw, @CurrentDate),
			day_of_year = DATENAME(dy, @CurrentDate),
			previous_day = DATEADD(DAY,-1,@CurrentDate),
			same_day_last_year = CAST(DATEADD(DAY, 1, DATEADD(YEAR, -1, DATEDIFF(DAY, '19000101', @CurrentDate))) AS DATE),
			day_name = LEFT(DATENAME(dw, @CurrentDate), 3)

		SET @CurrentDate = DATEADD(DD, 1, @CurrentDate)
	END

--=======================================================================================================================
	drop table if exists #tempDate
	select 
		date_id
		--,lag(weekid) over(order by date_id) weekid_prev
		,weekid
		,yearid
		,monid
		,cast(null as int) monid_min
		,cast(null as int) monid_max
		,cast(null as int) jlhWeek
	into #tempDate
	from(
		select date_id
			, datepart(iso_week,date_id) as weekid
			, year(date_id) yearid
			, month(date_id) monid
		from #temp_dim_date
		where date_id>='2019-12-01'
	)a
	--order by date_id

	update a set
		a.yearid=b.yearid
		,a.monid=b.monid
	from #tempDate a
	inner join (
		select 
			yearid
			,monid
			,max(weekid) weekid
		from #tempDate where monid=12
		group by yearid,monid
	)b on (a.yearid=(b.yearid+1) and a.weekid=b.weekid)
	where a.monid=1

	update #tempDate set 
		yearid=yearid+1
		,monid=1
	where weekid=1 and monid=12

	update a set
		a.monid_min=b.monid_min
		,a.monid_max=b.monid_max
	from #tempDate a inner join (
		select 
			yearid
			,weekid
			,min(monid) monid_min
			,max(monid) monid_max
		from #tempDate
		group by yearid, weekid
	)b on (a.yearid=b.yearid and a.weekid=b.weekid)

	update a set
		a.monid=case when b.monid_min_count>b.monid_max_count then b.monid_min else b.monid_max end
	from #tempDate a inner join (
		select 
			yearid
			,weekid
			,monid_min
			,monid_max
			,SUM(case when monid=monid_min then 1 else 0 end) monid_min_count
			,SUM(case when monid=monid_max then 1 else 0 end) monid_max_count
		from #tempDate 
		where 0=(case when monid_min=monid_max then 1 else 0 end)
		group by 
			yearid
			,weekid
			,monid_min
			,monid_max
	)b on (a.yearid=b.yearid and a.weekid=b.weekid and a.monid_min=b.monid_min and a.monid_max=b.monid_max)

	update a set a.jlhWeek=b.jlhWeek
	from #tempDate a inner join (
		select yearid, monid, count(1) jlhWeek from(
			select 
				weekid
				,monid 
				,yearid
			from #tempDate
			group by
				weekid
				,monid
				,yearid
		)a group by yearid, monid
	)b on (a.yearid=b.yearid and a.monid=b.monid)


	update a set
		a.weekReset_Month_ID=b.weekReset_Month_ID
		,a.weekReset_Desc=b.WEEKRESET_DESC
	from #temp_dim_date a inner join (
		select date_id, yearid, monid, monid_str, weekReset 
			,concat(yearid,monid_str) weekReset_Month_ID
			,concat('W', weekReset, case when monid=1 then ' Jan'
								when monid=2 then ' Feb'
								when monid=3 then ' Mar'
								when monid=4 then ' Apr'
								when monid=5 then ' May'
								when monid=6 then ' Jun'
								when monid=7 then ' Jul'
								when monid=8 then ' Aug'
								when monid=9 then ' Sep'
								when monid=10 then ' Oct'
								when monid=11 then ' Nov'
								when monid=12 then ' Dec' end) WEEKRESET_DESC
		from(
			select date_id
				,yearid
				,monid
				,right(concat('0',monid),2) monid_str
				,dense_rank() over(partition by yearid, monid order by weekid) weekReset

			from #tempDate where date_id>='2020-01-01'
		)a
	)b on (a.DATE_ID=b.DATE_ID)

	drop table if exists #temp_new_weekid
	create table #temp_new_weekid
	(
		date_id date,
		week_id int
	)

	set @CurrentDate = '2019-01-01'
	set @EndDate = '2035-12-31'

	declare @startMonth varchar(2) = '01'
	while @CurrentDate <= @EndDate
	begin
		set datefirst 6;
		declare @firstWeek datetime  
		declare @weekNum int  
		declare @year int  
		set @year = datepart(year, @CurrentDate) + 1    
		set @firstWeek = convert(datetime, str(@year) + @startMonth + '04', 102)   
		set @firstWeek = dateadd(day, (1 - datepart(dw, @firstWeek)), @firstWeek)  
		while @CurrentDate < @firstWeek
		begin  
		  set @year = @year - 1  
		  set @firstWeek = convert(datetime, str(@year) + @startMonth + '04', 102)  
		  set @firstWeek = dateadd(day, (1 - datepart(dw, @firstWeek)), @firstWeek)  
		end  
		set @weekNum = (@year * 100)+((datediff(day, @firstweek, @CurrentDate) / 7) + 1)  
		
		insert into #temp_new_weekid
		select @CurrentDate, @weekNum

		SET @CurrentDate = DATEADD(DD, 1, @CurrentDate)
	end 
	
	update a
	set a.week_id = b.week_id
	from #temp_dim_date a
	inner join #temp_new_weekid b on a.date_id = b.date_id

	select * from #temp_dim_date

END
GO


