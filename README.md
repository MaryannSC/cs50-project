# Swimming Tracker
#### Video Demo: https://youtu.be/H2nY5VwWO4s
#### Description:
Users record the distance they swim per workout, view all swims, edit swims, and view the monthly and yearly totals for all swims in
yards, meters, or miles.

![Image of the Swimming Tracker](/static/swimTrackerHome.png)


#### Register:
  Users register for an account with an email address, first and last names, password, and preferred units (yards, meters, or miles).
  The program verifies the user has entered all requested fields, a unique email, and a password that must have at least 8 characters,
  1 uppercase, 1 lowercase, and 1 special character.

  ![Image of registration page](/static/register.png)


#### Log In:
  Registered users log in with email and password.

  ![Image of log in page](/static/login.png)


#### Log Swims:
  Users log swims by entering date of swim, distance, and select units of distance.  The program verifies that all fields are filled and
  also checks that the date entered is not in the future.

  ![Image of Log Swims](/static/logSwims.png)


#### View All Swims:
  Users view all entered swims, most recent swim displayed first.

  ![Image of View All Swims](/static/viewSwims.png)


#### Edit Logged Swims:
  Users can delete an entry by clicking on the red 'X'.

  ![Image of Edit Logged Swims](/static/editSwims.png)


#### View Monthly Totals:
  Users view their total monthly distance grouped by year and also their yearly totals in their preferred units of distance.

  ![Image of View Monthly Totals](/static/monthlyTotals.png)


#### Preferences:
  Users can change the preferred unit of distance for displaying their total.  This is updated in the database for the next time
  the user logs in.

  ![Image of Preferences](/static/preferences.png)





### Under the hood - notes on the code:
  This project was based on C$50 finance and reused the framework.

  SQLite3 was used for the database.  ***swimTracker.db*** consists of 2 tables: ***users*** and ***swims***.

  ***users*** consists of a *userid* (primary key), *email*, *hash* (password), *firstName*, *lastName*, and *units*.  The users
  preferred units for displaying their totals is stored in *units*.

  ***swims*** consists of *swimid* (primary key), *userid*, *date*, *meters*, *miles*, *yards*, and *enteredunits*.  Users can log
  their swim distances in meters, miles, or yards.  The distance entered is converted to the other units and stored.  The original
  units are logged in *enteredunits*.  Storing the converted distances in the database greatly simplified summing and grouping the
  monthly and yearly totals versus converting and grouping in the main program.  The original units are preserved for display
  in ***View All Swims***.

   When logging a new swim, the program checks that the date entered is not in the future.  The date that is collected from ***Log Swims***
   has a time that is all zeros.  This could cause certain times to look like they were in the future when in fact they were the same day.
   When getting the current date, the time values were set to all zeros to avoid this problem and ensure only the dates were being compared.