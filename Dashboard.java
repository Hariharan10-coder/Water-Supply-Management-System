<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<title>
Water Supply Management Dashboard
</title>

<link rel="stylesheet" href="style.css">

</head>


<body>


<div class="dashboard">


<div class="topbar">

<div>
<h1>
Water Supply Management System
</h1>

<p>
Smart Water Monitoring Dashboard
</p>

</div>


<button onclick="logout()">
Logout
</button>


</div>



<div class="stats">


<div class="stat-card">

<div class="circle blue">
W
</div>

<div>
<h3>
Water Status
</h3>

<p class="active">
ACTIVE
</p>
</div>

</div>



<div class="stat-card">

<div class="circle cyan">
S
</div>

<div>
<h3>
Supply Units
</h3>

<p>
1200 Units
</p>

</div>

</div>




<div class="stat-card">

<div class="circle green">
U
</div>

<div>

<h3>
Registered Users
</h3>

<p>
500 Users
</p>

</div>

</div>



<div class="stat-card">

<div class="circle orange">
P
</div>

<div>

<h3>
Pressure Level
</h3>

<p>
Normal
</p>

</div>

</div>



</div>





<div class="content">


<div class="box">


<h2>
Water Distribution Overview
</h2>


<table>

<tr>

<th>
Area
</th>

<th>
Status
</th>

<th>
Consumption
</th>

</tr>


<tr>

<td>
Main Reservoir
</td>

<td class="active">
Running
</td>

<td>
850 KL
</td>

</tr>



<tr>

<td>
North Zone
</td>

<td class="active">
Normal
</td>

<td>
350 KL
</td>

</tr>




<tr>

<td>
South Zone
</td>

<td>
Maintenance
</td>

<td>
200 KL
</td>

</tr>


</table>


</div>






<div class="box">


<h2>
Recent Activities
</h2>


<ul>

<li>
System started successfully
</li>

<li>
Water supply checked
</li>

<li>
New user registered
</li>

<li>
Daily report generated
</li>

</ul>


</div>



</div>






<div class="footer">

Water Supply Management System © 2026

</div>



</div>





<script>

function logout()
{
window.location.href="index.html";
}

</script>


</body>

</html>