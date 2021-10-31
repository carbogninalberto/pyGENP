segmentsAcked = (int) (17.78-(1.21)-(8.04)-(5.31));
segmentsAcked = (int) (12.87+(12.01)+(14.87));
if (segmentsAcked > tcb->m_segmentSize) {
	tcb->m_cWnd = (int) (19.96*(5.1)*(18.36));

} else {
	tcb->m_cWnd = (int) (0.53*(15.76)*(18.58)*(segmentsAcked));

}
segmentsAcked = (int) (6.56+(13.05)+(5.28));
tcb->m_segmentSize = (int) (1.06+(3.49)+(3.64)+(10.0));
if (tcb->m_segmentSize != tcb->m_cWnd) {
	tcb->m_segmentSize = (int) (7.43-(16.29)-(12.94));

} else {
	tcb->m_segmentSize = (int) (11.61+(10.43));

}
if (segmentsAcked > tcb->m_cWnd) {
	tcb->m_cWnd = (int) (14.63-(18.61)-(tcb->m_segmentSize));

} else {
	tcb->m_cWnd = (int) (2.95*(6.07)*(tcb->m_cWnd));

}
if (tcb->m_cWnd == segmentsAcked) {
	segmentsAcked = (int) (10.38-(10.48)-(segmentsAcked));

} else {
	segmentsAcked = (int) (5.53+(tcb->m_cWnd)+(0.22)+(11.31));

}
