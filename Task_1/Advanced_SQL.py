"""
The database loan.db consists of 5 tables:
   1. customers - table containing customer data
   2. loans - table containing loan data pertaining to customers
   3. credit - table containing credit and creditscore data pertaining to customers
   4. repayments - table containing loan repayment data pertaining to customers
   5. months - table containing month name and month ID data

You are required to make use of your knowledge in SQL to query the database object (saved as loan.db) and return the requested information.
Simply fill in the vacant space wrapped in triple quotes per question (each function represents a question)

NOTE:
The database will be reset when grading each section. Any changes made to the database in the previous `SQL` section can be ignored.
Each question in this section is isolated unless it is stated that questions are linked.
Remember to clean your data

"""


def question_1():
    """
    Make use of a JOIN to find the `AverageIncome` per `CustomerClass`
    """

    qry = """
    -- I found exact duplicate rows in both the customers and credit tables, so I removed them before joining
    SELECT cr.CustomerClass, AVG(cu.Income) AS AverageIncome
    FROM (SELECT DISTINCT * FROM customers) cu
    JOIN (SELECT DISTINCT * FROM credit) cr
        ON cu.CustomerID = cr.CustomerID
    GROUP BY cr.CustomerClass
    ORDER BY cr.CustomerClass
    """

    return qry


def question_2():
    """
    Make use of a JOIN to return a breakdown of the number of 'RejectedApplications' per 'Province'.
    Ensure consistent use of either the abbreviated or full version of each province, matching the format found in the customer table.
    """

    qry = """
    -- Most customers (941 of 1000) use the abbreviated province names, so I standardised the full names to abbreviations
    -- I found exact duplicate rows in the customers and loans tables, so I removed them before joining
    SELECT
        CASE cu.Region
            WHEN 'EasternCape'   THEN 'EC'
            WHEN 'FreeState'     THEN 'FS'
            WHEN 'Gauteng'       THEN 'GT'
            WHEN 'KwaZulu-Natal' THEN 'KZN'
            WHEN 'Limpopo'       THEN 'LP'
            WHEN 'Mpumalanga'    THEN 'MP'
            WHEN 'NorthernCape'  THEN 'NC'
            WHEN 'NorthWest'     THEN 'NW'
            WHEN 'WesternCape'   THEN 'WC'
            ELSE cu.Region
        END AS Province,
        COUNT(*) AS RejectedApplications
    FROM (SELECT DISTINCT * FROM customers) cu
    JOIN (SELECT DISTINCT * FROM loans) lo
        ON cu.CustomerID = lo.CustomerID
    WHERE lo.ApprovalStatus = 'Rejected'
    GROUP BY Province
    ORDER BY Province
    """

    return qry


def question_3():
    """
    Making use of the `INSERT` function, create a new table called `financing` which will include the following columns:
    `CustomerID`,`Income`,`LoanAmount`,`LoanTerm`,`InterestRate`,`ApprovalStatus` and `CreditScore`

    Do not return the new table, just create it.
    """

    qry = """
    -- I removed exact duplicate rows from all three source tables before joining, so each customer appears once
    -- CREATE OR REPLACE lets the query be rerun without failing on an existing table
    CREATE OR REPLACE TABLE financing (
        CustomerID     INTEGER,
        Income         INTEGER,
        LoanAmount     INTEGER,
        LoanTerm       INTEGER,
        InterestRate   FLOAT,
        ApprovalStatus VARCHAR,
        CreditScore    INTEGER
    );

    INSERT INTO financing
    SELECT cu.CustomerID, cu.Income, lo.LoanAmount, lo.LoanTerm, lo.InterestRate, lo.ApprovalStatus, cr.CreditScore
    FROM (SELECT DISTINCT * FROM customers) cu
    JOIN (SELECT DISTINCT * FROM loans)  lo ON cu.CustomerID = lo.CustomerID
    JOIN (SELECT DISTINCT * FROM credit) cr ON cu.CustomerID = cr.CustomerID;
    """

    return qry


# Question 4 and 5 are linked


def question_4():
    """
    Using a `CROSS JOIN` and the `months` table, create a new table called `timeline` that sumarises Repayments per customer per month.
    Columns should be: `CustomerID`, `MonthName`, `NumberOfRepayments`, `AmountTotal`.
    Repayments should only occur between 6am and 6pm London Time.
    Null values to be filled with 0.

    Hint: there should be 12x CustomerID = 1.
    """

    qry = """
    -- Assumption: each RepaymentDate is local time in its TimeZone column
    -- Assumption: the abbreviations follow the standard Java/ICU short IDs (e.g. IST = India, CST = US Central, PNT = Phoenix), since abbreviations like IST and CST are ambiguous and this is the only standard set that defines all nine codes
    -- I mapped them to full time zone names so daylight saving is handled correctly for both the source zone and London
    -- The 6am-6pm filter is in the LEFT JOIN's ON clause so customer-months with no repayments are kept as 0
    CREATE OR REPLACE TABLE timeline AS
    WITH tz_map AS (
        SELECT * FROM (VALUES
            ('CET', 'Europe/Paris'),
            ('CST', 'America/Chicago'),
            ('EET', 'Europe/Athens'),
            ('GMT', 'GMT'),
            ('IST', 'Asia/Kolkata'),
            ('JST', 'Asia/Tokyo'),
            ('PNT', 'America/Phoenix'),
            ('PST', 'America/Los_Angeles'),
            ('UTC', 'UTC')
        ) AS t(TimeZone, ZoneName)
    ),
    london_repayments AS (
        SELECT
            r.CustomerID,
            r.Amount,
            (r.RepaymentDate AT TIME ZONE z.ZoneName) AT TIME ZONE 'Europe/London' AS LondonTime
        FROM repayments r
        JOIN tz_map z ON r.TimeZone = z.TimeZone
    )
    SELECT
        c.CustomerID,
        m.MonthName,
        COUNT(lr.Amount)                             AS NumberOfRepayments,
        CAST(COALESCE(SUM(lr.Amount), 0) AS INTEGER) AS AmountTotal
    FROM (SELECT DISTINCT CustomerID FROM customers) c
    CROSS JOIN months m
    LEFT JOIN london_repayments lr
        ON  lr.CustomerID = c.CustomerID
        AND MONTH(lr.LondonTime) = m.MonthID
        AND CAST(lr.LondonTime AS TIME) BETWEEN '06:00:00' AND '18:00:00'
    GROUP BY c.CustomerID, m.MonthID, m.MonthName
    ORDER BY c.CustomerID, m.MonthID
    """

    return qry


def question_5():
    """
    Make use of conditional aggregation to pivot the `timeline` table such that the columns are as follows:
    `CustomerID`, `JanuaryRepayments`, `JanuaryTotal`,...,`DecemberRepayments`, `DecemberTotal`,...etc
    MonthRepayments columns (e.g JanuaryRepayments) should be integers

    Hint: there should be 1x CustomerID = 1
    """

    qry = """
    -- timeline has exactly one row per customer per month, so each SUM(CASE ...) just picks out that month's value
    -- SUM returns a very large integer type that pandas displays as decimals, so I cast the results back to INTEGER
    SELECT
        CustomerID,
        CAST(SUM(CASE WHEN MonthName = 'January'   THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS JanuaryRepayments,
        CAST(SUM(CASE WHEN MonthName = 'January'   THEN AmountTotal        ELSE 0 END) AS INTEGER) AS JanuaryTotal,
        CAST(SUM(CASE WHEN MonthName = 'February'  THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS FebruaryRepayments,
        CAST(SUM(CASE WHEN MonthName = 'February'  THEN AmountTotal        ELSE 0 END) AS INTEGER) AS FebruaryTotal,
        CAST(SUM(CASE WHEN MonthName = 'March'     THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS MarchRepayments,
        CAST(SUM(CASE WHEN MonthName = 'March'     THEN AmountTotal        ELSE 0 END) AS INTEGER) AS MarchTotal,
        CAST(SUM(CASE WHEN MonthName = 'April'     THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS AprilRepayments,
        CAST(SUM(CASE WHEN MonthName = 'April'     THEN AmountTotal        ELSE 0 END) AS INTEGER) AS AprilTotal,
        CAST(SUM(CASE WHEN MonthName = 'May'       THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS MayRepayments,
        CAST(SUM(CASE WHEN MonthName = 'May'       THEN AmountTotal        ELSE 0 END) AS INTEGER) AS MayTotal,
        CAST(SUM(CASE WHEN MonthName = 'June'      THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS JuneRepayments,
        CAST(SUM(CASE WHEN MonthName = 'June'      THEN AmountTotal        ELSE 0 END) AS INTEGER) AS JuneTotal,
        CAST(SUM(CASE WHEN MonthName = 'July'      THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS JulyRepayments,
        CAST(SUM(CASE WHEN MonthName = 'July'      THEN AmountTotal        ELSE 0 END) AS INTEGER) AS JulyTotal,
        CAST(SUM(CASE WHEN MonthName = 'August'    THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS AugustRepayments,
        CAST(SUM(CASE WHEN MonthName = 'August'    THEN AmountTotal        ELSE 0 END) AS INTEGER) AS AugustTotal,
        CAST(SUM(CASE WHEN MonthName = 'September' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS SeptemberRepayments,
        CAST(SUM(CASE WHEN MonthName = 'September' THEN AmountTotal        ELSE 0 END) AS INTEGER) AS SeptemberTotal,
        CAST(SUM(CASE WHEN MonthName = 'October'   THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS OctoberRepayments,
        CAST(SUM(CASE WHEN MonthName = 'October'   THEN AmountTotal        ELSE 0 END) AS INTEGER) AS OctoberTotal,
        CAST(SUM(CASE WHEN MonthName = 'November'  THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS NovemberRepayments,
        CAST(SUM(CASE WHEN MonthName = 'November'  THEN AmountTotal        ELSE 0 END) AS INTEGER) AS NovemberTotal,
        CAST(SUM(CASE WHEN MonthName = 'December'  THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS DecemberRepayments,
        CAST(SUM(CASE WHEN MonthName = 'December'  THEN AmountTotal        ELSE 0 END) AS INTEGER) AS DecemberTotal
    FROM timeline
    GROUP BY CustomerID
    ORDER BY CustomerID
    """

    return qry


# QUESTION 6 and 7 are linked, Do not be concerned with timezones or repayment times for these question.


def question_6():
    """
    The `customers` table was created by merging two separate tables: one containing data for male customers and the other for female customers.
    Due to an error, the data in the age columns were misaligned in both original tables, resulting in a shift of two places upwards in
    relation to the corresponding CustomerID.

    Create a table called `corrected_customers` with columns: `CustomerID`, `Age`, `CorrectedAge`, `Gender`
    Utilize a window function to correct this mistake in the new `CorrectedAge` column.
    Null values can be input manually - i.e. values that overflow should loop to the top of each gender.

    Also return a result set for this table (ie SELECT * FROM corrected_customers)
    """

    qry = """
    -- I removed exact duplicate rows first, since an extra copy would throw off every position after it in the shift
    -- The ages are shifted within each original gender table, so I partitioned by Gender and used LAG(Age, 2) to move each age back down to its owner
    -- LAG leaves the first two customers of each gender empty, so I wrapped the last two ages of that gender around to fill them
    CREATE OR REPLACE TABLE corrected_customers AS
    SELECT
        CustomerID,
        Age,
        COALESCE(
            LAG(Age, 2) OVER w,
            CASE ROW_NUMBER() OVER w
                WHEN 1 THEN NTH_VALUE(Age, 2) OVER w_reversed
                WHEN 2 THEN NTH_VALUE(Age, 1) OVER w_reversed
            END
        ) AS CorrectedAge,
        Gender
    FROM (SELECT DISTINCT * FROM customers)
    WINDOW
        w          AS (PARTITION BY Gender ORDER BY CustomerID),
        w_reversed AS (PARTITION BY Gender ORDER BY CustomerID DESC
                       ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING);
    
    SELECT * FROM corrected_customers
    ORDER BY CustomerID;
    """

    return qry


def question_7():
    """
    Create a column in corrected_customers called 'AgeCategory' that categorizes customers by age.
    Age categories should be as follows:
        - `Teen`: CorrectedAge < 20
        - `Young Adult`: 20 <= CorrectedAge < 30
        - `Adult`: 30 <= CorrectedAge < 60
        - `Pensioner`: CorrectedAge >= 60

    Make use of a windows function to assign a rank to each customer based on the total number of repayments per age group. Add this into a "Rank" column.
    The ranking should not skip numbers in the sequence, even when there are ties, i.e. 1,2,2,2,3,4 not 1,2,2,2,5,6
    Customers with no repayments should be included as 0 in the result.

    Return columns: `CustomerID`, `Age`, `CorrectedAge`, `Gender`, `AgeCategory`, `Rank`
    """

    qry = """
    -- Assumption: rank 1 goes to the customer with the most repayments in their age category
    -- I counted all repayments regardless of time, and used a LEFT JOIN with COUNT(RepaymentID) so customers without repayments get 0
    -- IF NOT EXISTS lets the query be rerun without failing on the existing AgeCategory column
    ALTER TABLE corrected_customers ADD COLUMN IF NOT EXISTS AgeCategory VARCHAR;

    UPDATE corrected_customers
    SET AgeCategory = CASE
        WHEN CorrectedAge < 20 THEN 'Teen'
        WHEN CorrectedAge < 30 THEN 'Young Adult'
        WHEN CorrectedAge < 60 THEN 'Adult'
        ELSE 'Pensioner'
    END;
    
    SELECT
        cc.CustomerID,
        cc.Age,
        cc.CorrectedAge,
        cc.Gender,
        cc.AgeCategory,
        DENSE_RANK() OVER (
            PARTITION BY cc.AgeCategory
            ORDER BY COUNT(r.RepaymentID) DESC
        ) AS "Rank"
    FROM corrected_customers cc
    LEFT JOIN repayments r ON r.CustomerID = cc.CustomerID
    GROUP BY cc.CustomerID, cc.Age, cc.CorrectedAge, cc.Gender, cc.AgeCategory
    ORDER BY cc.AgeCategory, "Rank", cc.CustomerID;
    """

    return qry
