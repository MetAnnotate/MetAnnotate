unless (@ARGV)
{	print "usage: perl $0 <list to remove> <fasta>\n";
}

open FILE,$ARGV[0];
while (<FILE>)
{	chomp;
	$_ = ">" . $_;
	$seen{$_} = 1;
}

close FILE;

open FILE,$ARGV[1];
while (<FILE>)
{	chomp;
	if (substr($_,0,1) eq ">")
	{	if ( $seen{$_} )
		{	$print = 0;
	
		}
		else
		{	$print = 1;
			print;
			print "\n";
		}
	}
	else
	{	if ( $print == 1 )
		{	print;
			print "\n";
		}
	}
	
}
