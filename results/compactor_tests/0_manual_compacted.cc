segmentsAcked = SlowStart (tcb, segmentsAcked);
ReduceCwnd (tcb);
for (int i = 0; i < 4; i++) { 
	segmentsAcked = SlowStart (tcb, segmentsAcked);
}
if (tcb->m_segmentSize < tcb->m_cWnd) {
segmentsAcked = (int) (14.163*(1.548)*(90.037)*(31.269));

} else {
segmentsAcked = (int) (95.874+(6.459)+(25.604)+(67.102)+(79.782)+(14.508)+(77.982));
segmentsAcked = SlowStart (tcb, segmentsAcked);

}

for (int i = 0; i < 3; i++) { 
	segmentsAcked = SlowStart (tcb, segmentsAcked);
}

for (int i = 0; i < 2; i++) { 
	segmentsAcked = SlowStart (tcb, segmentsAcked);
}

segmentsAcked = SlowStart (tcb, segmentsAcked);
ReduceCwnd (tcb);

for (int i = 0; i < 5; i++) { 
	segmentsAcked = SlowStart (tcb, segmentsAcked);
}

if (tcb->m_segmentSize < tcb->m_cWnd) {
segmentsAcked = (int) (95.874+(6.459)+(25.604)+(67.102)+(79.782)+(14.508)+(77.982));
segmentsAcked = SlowStart (tcb, segmentsAcked);

} else {
segmentsAcked = (int) (14.163*(1.548)*(90.037)*(31.269));

}

for (int i = 0; i < 11; i++) { 
	segmentsAcked = SlowStart (tcb, segmentsAcked);
}