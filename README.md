# INVESTMENT ACCOUNT MANAGER APP

|Tool                | Description                    | Tags for tools used                                                                                               |
| ------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------------- |
| 1.GitHub| Version Control and CI/CD| [Version-Control]; [Repo]; [Pipeline]; [Continuous integration];[Continuous Delivery]|
| 2.Django |  Python Based Backend Framework| [python]; [Django];|
| 3.PostgresQl | Relational Database| [Relational Integrity]; [Database];|
| 4.Pipenv | Package/Dependency manager| [Virtual Environment];[Dependency];|

## <h1> Description</h1>
<p>The aim of the project is to build a DRF (Django Rest Framework) for an investment account management API built using Python's Django framework </p>
<p>The project enables Users to create Investment accounts with different levels: 
Account 1: Enables view rights.
Account 2: Enables CRUD (Create, Read, Update, Delete) permissions
Account 3: Enables only users to only post transactions</p>

## <h1> Features</h1>
<ul>
<li> Admin dashboard: The admin dashboard enables a staff user to add and remove users.
    create investment accounts, allocate and revoke user permissions and to view transactions </li>
<li> Authentication:  authentication token that enable a user to sign up and log in,create accounts and carry out any transactions </li>
<li> Transaction simulation: A user can simulate transaction of different investments, start with an account balance of 20,000 in account and view balance remaining on transaction.Alpha Vantage API has been intergrated to calculate real time price/unit of investments
An exchange rate of 1 usd = kes.140 has been used to calculate the amounts.
</li>
<li> Market Data API: An API from Alpha vantage simulating market data has been intergrated to monitor data</li>
</ul>

## <h1> Set up Instructions</h1>
<p><b>Github</b></p>
<ul>
<li> Download the Zip file from the code tab on github to get the project Zip files (Recommended)</li>
<li> Clone the project using 'git clone https://github.com/andreindeche/InvestManager.git'.</li>
<li> Unzip the file and add the Project folder to your IDE/Compiler</li>
</ul>

1. Create an .env environment on the Django root folder and add the recessary environment variables. 
Use <b>env.example</b> as a guide for environment variables.

<p><b>Django</b></p>
<p>The project uses pipenv, django and postgresql backend</p>

1. Install pipenv using the command 

```bash
pip install pipenv
```

2. Activate your virtual enviromnment

```bash
pipenv shell 
```

3. Naviagte to your Django project and use  in  the directory path: <b>backend\requirements.txt</b> to install the required django dependencies 

```bash
pipenv install -r requirements.txt
```

4. Create an .env on the Django root folder and add the recessary environment variables. 

Use (backend\env.example) as a guide for environment variables </li>

5. Create a Super User using 

```bash
python manage.py createsuperuser
```

6. Migrate your DB using 

```bash
python manage.py migrate
```

7. To run the project outside of a shell environment use: 

```bash
pipenv run python manage.py runserver
```

 or while in the shell environment use:

```bash
python manage.py runserver
```

## <h1> Endpoints</h1>
Use Postman API platform or any other alternative to test the API End Points

1. Create User Account:
    Fields: "username", "password", "confirm_password",
    POST: /api/register/

2. Log into account:
    Fields: "username", "password",
    POST: /api/login/

3.Create Investment Account:
    Fields: "name", "description", "users" , "permission"- "view","POST,or "full" 
    POST: /api/accounts/

4.List Investment Accounts:
    GET: /api/accounts/

5.Retrieve Account:
    Use account id for retrieval
    GET  /api/accounts/{int:pk}/

6.Update Account: 
    Use account id for retrieval
    Fields: "name", "description", "users" , "permission"- "view","POST,or "full" 
    PUT /api/accounts/{pk}/

7.Delete Account: 
    DELETE /api/accounts/{pk}/

8.List Permissions: 
    GET /api/account-permissions/

9.Create Permission: 
    Fields: "user": testuser, "account": Test Account, "permission" - "view","POST,or "full" 
    POST /api/account-permissions/ (Admins can use this to assign permissions)

10.Retrieve Permission: 
    GET /api/account-permissions/{pk}/

11.Update Permission: 
    Fields: "user": testuser, "account": Test Account, "permission"- "view","POST,or "full" 
    PUT /api/account-permissions/{pk}/ (Admins can use this to update permissions)

12.Delete Permission: 
    DELETE /api/account-permissions/{pk}/ (Admins can use this to delete permissions)

13.Select Current Account: 
    PUT /api/select-account/{pk}/ (Users can use this to set their current account)

## SYMBOLS FOR INVESTMENT
    navigate to: https://www.alphavantage.co/documentation/ for more symbols

    Stock symbols: IBM, AAPL (Apple), MSFT (Microsoft)
    Forex Symbols: FROM/TO e.g. EUR/USD for Euro to US Dollar2.
    Cryptocurrency Symbols: FROM/TO e.g. BTC/USD

14.Buy and Sell Investments:
    Starting balance is: 20,000, view balance in account 
    Fields: "transaction_type": "buy","amount": 10,"symbol": "AAPL"
    POST /accounts/<account_pk>/investments/simulate/

15. Admin Endpoint to view Transactions
    Filtering range: /?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    GET admin/transactions/<str:username>/

16.Fetch Market data for selected investment
    PARAMS: Stock symbols, Forex Symbols, Cryptocurrence Symbols
    GET /api/market-data/<str:data_type>/{symbol}

## <h1> Author </h1>
Built by <b>Andrew Indeche</b>