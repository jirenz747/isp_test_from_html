<html>

<head>
	<meta http-equiv="Content-Type"  content="text/html; charset=windows-1251">
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.2.0/jquery.min.js"></script>
	<style>
	.load {text-align: center; display: none;}
	</style>
</head>

<body>

<form name="form1" action="http://dc-nagios01/cgi-bin/isp_test_from_html/isp_test_from_html.py" method="get">
<br><br><br><br>
<table border="1"  align="center">


        <tr border="0">
	 <td  align="center">
	Введите имя объекта. (пример mos12)
	</td>
	<td>
	<input id="text_1" type="text" name="hostname" value="" style="width: 200px;">
	</td>
</tr>
<tr>
<td colspan="2" align="center">
<input id="send_1" type="button" onclick="submitForm1('http://dc-nagios01/cgi-bin/isp_test_from_html/isp_test_from_html.py')"  value="send">

<script type="text/javascript"> 
		function submitForm1(action) {
			$('#send_1').prop('disabled', true);
			$('.load').show();
			document.forms['form1'].action = action;
			document.forms['form1'].submit();
		}
	</script>
</td>
</tr>
</table>


</form>
<br><br>
<center><a href="http://dc-nagios01/"> Назад </a></center>
</body>

</html>

