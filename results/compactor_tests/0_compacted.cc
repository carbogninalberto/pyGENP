segmentsAcked = SlowStart (tcb, segmentsAcked);
ReduceCwnd (tcb);

for (int i = 0; i < 4; i++) { 
	segmentsAcked = SlowStart (tcb, segmentsAcked);
}

if (tcb->m_segmentSize < tcb->m_cWnd) {
segmentsAcked = (int) 61725.01725646478;
} else {
segmentsAcked = (int) 367.3109999999999;
segmentsAcked = SlowStart (tcb, segmentsAcked);
}

for (int i = 0; i < 6; i++) { 
	segmentsAcked = SlowStart (tcb, segmentsAcked);
}

ReduceCwnd (tcb);

for (int i = 0; i < 5; i++) { 
	segmentsAcked = SlowStart (tcb, segmentsAcked);
}

if (tcb->m_segmentSize < tcb->m_cWnd) {
segmentsAcked = (int) 367.3109999999999;
segmentsAcked = SlowStart (tcb, segmentsAcked);
} else {
segmentsAcked = (int) 61725.01725646478;
}

for (int i = 0; i < 11; i++) { 
	segmentsAcked = SlowStart (tcb, segmentsAcked);
}

