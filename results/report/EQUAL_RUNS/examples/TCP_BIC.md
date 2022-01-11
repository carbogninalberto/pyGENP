## Examples of Baseline vs Best Individuals


### BIC Baseline

```c++
/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2014 Natale Patriciello <natale.patriciello@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 */
#include "tcp-bic.h"
#include "ns3/log.h"
#include "ns3/simulator.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("TcpBic");
NS_OBJECT_ENSURE_REGISTERED (TcpBic);

TypeId
TcpBic::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::TcpBic")
    .SetParent<TcpCongestionOps> ()
    .AddConstructor<TcpBic> ()
    .SetGroupName ("Internet")
    .AddAttribute ("FastConvergence", "Turn on/off fast convergence.",
                   BooleanValue (true),
                   MakeBooleanAccessor (&TcpBic::m_fastConvergence),
                   MakeBooleanChecker ())
    .AddAttribute ("Beta", "Beta for multiplicative decrease",
                   DoubleValue (0.8),
                   MakeDoubleAccessor (&TcpBic::m_beta),
                   MakeDoubleChecker <double> (0.0))
    .AddAttribute ("MaxIncr", "Limit on increment allowed during binary search",
                   UintegerValue (16),
                   MakeUintegerAccessor (&TcpBic::m_maxIncr),
                   MakeUintegerChecker <uint32_t> (1))
    .AddAttribute ("LowWnd", "Threshold window size (in segments) for engaging BIC response",
                   UintegerValue (14),
                   MakeUintegerAccessor (&TcpBic::m_lowWnd),
                   MakeUintegerChecker <uint32_t> ())
    .AddAttribute ("SmoothPart", "Number of RTT needed to approach cWnd_max from "
                   "cWnd_max-BinarySearchCoefficient. It can be viewed as the gradient "
                   "of the slow start AIM phase: less this value is, "
                   "more steep the increment will be.",
                   UintegerValue (5),
                   MakeUintegerAccessor (&TcpBic::m_smoothPart),
                   MakeUintegerChecker <uint32_t> (1))
    .AddAttribute ("BinarySearchCoefficient", "Inverse of the coefficient for the "
                   "binary search. Default 4, as in Linux",
                   UintegerValue (4),
                   MakeUintegerAccessor (&TcpBic::m_b),
                   MakeUintegerChecker <uint8_t> (2))
  ;
  return tid;
}


TcpBic::TcpBic ()
  : TcpCongestionOps (),
    m_cWndCnt (0),
    m_lastMaxCwnd (0),
    m_lastCwnd (0),
    m_epochStart (Time::Min ())
{
  NS_LOG_FUNCTION (this);
}

TcpBic::TcpBic (const TcpBic &sock)
  : TcpCongestionOps (sock),
    m_fastConvergence (sock.m_fastConvergence),
    m_beta (sock.m_beta),
    m_maxIncr (sock.m_maxIncr),
    m_lowWnd (sock.m_lowWnd),
    m_smoothPart (sock.m_smoothPart),
    m_cWndCnt (sock.m_cWndCnt),
    m_lastMaxCwnd (sock.m_lastMaxCwnd),
    m_lastCwnd (sock.m_lastCwnd),
    m_epochStart (sock.m_epochStart),
    m_b (sock.m_b)
{
  NS_LOG_FUNCTION (this);
}


// This is the target function
void
TcpBic::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);

  if (tcb->m_cWnd < tcb->m_ssThresh)
    {
      tcb->m_cWnd += tcb->m_segmentSize;
      segmentsAcked -= 1;

      NS_LOG_INFO ("In SlowStart, updated to cwnd " << tcb->m_cWnd <<
                   " ssthresh " << tcb->m_ssThresh);
    }

  if (tcb->m_cWnd >= tcb->m_ssThresh && segmentsAcked > 0)
    {
      m_cWndCnt += segmentsAcked;
      uint32_t cnt = Update (tcb);

      /* According to the BIC paper and RFC 6356 even once the new cwnd is
       * calculated you must compare this to the number of ACKs received since
       * the last cwnd update. If not enough ACKs have been received then cwnd
       * cannot be updated.
       */
      if (m_cWndCnt > cnt)
        {
          tcb->m_cWnd += tcb->m_segmentSize;
          m_cWndCnt = 0;
          NS_LOG_INFO ("In CongAvoid, updated to cwnd " << tcb->m_cWnd);
        }
      else
        {
          NS_LOG_INFO ("Not enough segments have been ACKed to increment cwnd."
                       "Until now " << m_cWndCnt);
        }
    }


}

uint32_t
TcpBic::Update (Ptr<TcpSocketState> tcb)
{
  NS_LOG_FUNCTION (this << tcb);

  uint32_t segCwnd = tcb->GetCwndInSegments ();
  uint32_t cnt;

  m_lastCwnd = segCwnd;

  if (m_epochStart == Time::Min ())
    {
      m_epochStart = Simulator::Now ();   /* record the beginning of an epoch */
    }

  if (segCwnd < m_lowWnd)
    {
      NS_LOG_INFO ("Under lowWnd, compatibility mode. Behaving as NewReno");
      cnt = segCwnd;
      return cnt;
    }

  if (segCwnd < m_lastMaxCwnd)
    {
      double dist = (m_lastMaxCwnd - segCwnd) / m_b;

      NS_LOG_INFO ("cWnd = " << segCwnd << " under lastMax, " <<
                   m_lastMaxCwnd << " and dist=" << dist);
      if (dist > m_maxIncr)
        {
          /* Linear increase */
          cnt = segCwnd / m_maxIncr;
          NS_LOG_INFO ("Linear increase (maxIncr=" << m_maxIncr << "), cnt=" << cnt);
        }
      else if (dist <= 1)
        {
          /* smoothed binary search increase: when our window is really
           * close to the last maximum, we parameterize in m_smoothPart the number
           * of RTT needed to reach that window.
           */
          cnt = (segCwnd * m_smoothPart) / m_b;

          NS_LOG_INFO ("Binary search increase (smoothPart=" << m_smoothPart <<
                       "), cnt=" << cnt);
        }
      else
        {
          /* binary search increase */
          cnt = static_cast<uint32_t> (segCwnd / dist);

          NS_LOG_INFO ("Binary search increase, cnt=" << cnt);
        }
    }
  else
    {
      NS_LOG_INFO ("cWnd = " << segCwnd << " above last max, " <<
                   m_lastMaxCwnd);
      if (segCwnd < m_lastMaxCwnd + m_b)
        {
          /* slow start AMD linear increase */
          cnt = (segCwnd * m_smoothPart) / m_b;
          NS_LOG_INFO ("Slow start AMD, cnt=" << cnt);
        }
      else if (segCwnd < m_lastMaxCwnd + m_maxIncr * (m_b - 1))
        {
          /* slow start */
          cnt = (segCwnd * (m_b - 1)) / (segCwnd - m_lastMaxCwnd);

          NS_LOG_INFO ("Slow start, cnt=" << cnt);
        }
      else
        {
          /* linear increase */
          cnt = segCwnd / m_maxIncr;

          NS_LOG_INFO ("Linear, cnt=" << cnt);
        }
    }

  /* if in slow start or link utilization is very low. Code taken from Linux
   * kernel, not sure of the source they take it. Usually, it is not reached,
   * since if m_lastMaxCwnd is 0, we are (hopefully) in slow start.
   */
  if (m_lastMaxCwnd == 0)
    {
      if (cnt > 20) /* increase cwnd 5% per RTT */
        {
          cnt = 20;
        }
    }

  if (cnt == 0)
    {
      cnt = 1;
    }

  return cnt;
}

std::string
TcpBic::GetName () const
{
  return "TcpBic";
}

uint32_t
TcpBic::GetSsThresh (Ptr<const TcpSocketState> tcb, uint32_t bytesInFlight)
{
  NS_LOG_FUNCTION (this);

  uint32_t segCwnd = tcb->GetCwndInSegments ();
  uint32_t ssThresh = 0;

  m_epochStart = Time::Min ();

  /* Wmax and fast convergence */
  if (segCwnd < m_lastMaxCwnd && m_fastConvergence)
    {
      NS_LOG_INFO ("Fast Convergence. Last max cwnd: " << m_lastMaxCwnd <<
                   " updated to " << static_cast<uint32_t> (m_beta * segCwnd));
      m_lastMaxCwnd = static_cast<uint32_t> (m_beta * segCwnd);
    }
  else
    {
      NS_LOG_INFO ("Last max cwnd: " << m_lastMaxCwnd << " updated to " <<
                   segCwnd);
      m_lastMaxCwnd = segCwnd;
    }

  if (segCwnd < m_lowWnd)
    {
      ssThresh = std::max (2 * tcb->m_segmentSize, bytesInFlight / 2);
      NS_LOG_INFO ("Less than lowWindow, ssTh= " << ssThresh);
    }
  else
    {
      ssThresh = static_cast<uint32_t> (std::max (segCwnd * m_beta, 2.0) * tcb->m_segmentSize);
      NS_LOG_INFO ("More than lowWindow, ssTh= " << ssThresh);
    }

  return ssThresh;
}

void
TcpBic::ReduceCwnd (Ptr<TcpSocketState> tcb)
{
  NS_LOG_FUNCTION (this << tcb);

  tcb->m_cWnd = std::max (tcb->m_cWnd.Get () / 2, tcb->m_segmentSize);
}

Ptr<TcpCongestionOps>
TcpBic::Fork (void)
{
  return CopyObject<TcpBic> (this);
}

} // namespace ns3

```

Bic `IncreaseWindow` is changed as follow:

```c++
void
TcpBic::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);

  // if (tcb->m_cWnd < tcb->m_ssThresh)
  //   {
  //     tcb->m_cWnd += tcb->m_segmentSize;
  //     segmentsAcked -= 1;

  //     NS_LOG_INFO ("In SlowStart, updated to cwnd " << tcb->m_cWnd <<
  //                  " ssthresh " << tcb->m_ssThresh);
  //   }

  // if (tcb->m_cWnd >= tcb->m_ssThresh && segmentsAcked > 0)
  //   {
  //     m_cWndCnt += segmentsAcked;
  //     uint32_t cnt = Update (tcb);

  //     /* According to the BIC paper and RFC 6356 even once the new cwnd is
  //      * calculated you must compare this to the number of ACKs received since
  //      * the last cwnd update. If not enough ACKs have been received then cwnd
  //      * cannot be updated.
  //      */
  //     if (m_cWndCnt > cnt)
  //       {
  //         tcb->m_cWnd += tcb->m_segmentSize;
  //         m_cWndCnt = 0;
  //         NS_LOG_INFO ("In CongAvoid, updated to cwnd " << tcb->m_cWnd);
  //       }
  //     else
  //       {
  //         NS_LOG_INFO ("Not enough segments have been ACKed to increment cwnd."
  //                      "Until now " << m_cWndCnt);
  //       }
  //   }
uint32_t cnt = Update (tcb);
char * individual = getenv("range");
if (individual != NULL) {
  switch(atoi(individual)) {
//REPLACE

//REPLACE

    default:
      break;
  }
}


}
```

Inside replace is pasted the individuals code and evaluated by reading the input variable.

Examples of Best individuals

run 1 gen 50 ind 29
```c++
void
TcpBic::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);

// generated
if (m_cWndCnt > cnt) {   tcb->m_cWnd += tcb->m_segmentSize;   m_cWndCnt = 0; }
float HlHWRlAtyKnWiHYm = (float) (((0.1)+(0.1)+(0.1)+(0.1))/((0.1)+(81.609)+(86.098)+(0.1)));
if (cnt != segmentsAcked) {
	tcb->m_cWnd = (int) ((((37.177+(14.08)+(39.77)))+(9.465)+((28.38+(33.705)))+((74.057*(41.363)*(84.148)*(56.919)))+(26.314)+(0.1)+(30.713))/((45.478)+(76.286)));

} else {
	tcb->m_cWnd = (int) (77.045-(34.08)-(83.867)-(96.84)-(61.981));

}
if (m_cWndCnt > cnt) {   tcb->m_cWnd += tcb->m_segmentSize;   m_cWndCnt = 0; }
ReduceCwnd (tcb);
// generated


}
```

run 2 gen 50 ind 29
```c++
void
TcpBic::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);

// generated
if (m_cWndCnt > cnt) {   tcb->m_cWnd += tcb->m_segmentSize;   m_cWndCnt = 0; }
if (tcb->m_cWnd >= segmentsAcked) {
	segmentsAcked = (int) (94.823-(97.369));
	ReduceCwnd (tcb);
	segmentsAcked = (int) (72.126/6.518);

} else {
	segmentsAcked = (int) (3.985*(60.818)*(57.572));
	cnt = (int) (75.543-(58.348)-(66.019)-(tcb->m_cWnd)-(39.143)-(30.801)-(55.39)-(68.035)-(tcb->m_segmentSize));

}
if (m_cWndCnt > cnt) {   tcb->m_cWnd += tcb->m_segmentSize;   m_cWndCnt = 0; }
tcb->m_cWnd = (int) (segmentsAcked-(47.737)-(34.522)-(62.265)-(67.195)-(tcb->m_ssThresh));
if (m_cWndCnt > cnt) {   tcb->m_cWnd += tcb->m_segmentSize;   m_cWndCnt = 0; }
if (tcb->m_segmentSize != tcb->m_cWnd) {
	segmentsAcked = (int) (((86.801)+(53.357)+(21.778)+(0.1)+(30.347))/((0.1)+(37.232)));
	tcb->m_cWnd = (int) (40.8*(48.345)*(25.506));
	segmentsAcked = (int) ((78.93+(74.413)+(98.714)+(14.724))/0.1);

} else {
	segmentsAcked = (int) (55.228-(41.347)-(89.556)-(24.773)-(24.989)-(tcb->m_cWnd)-(33.413));
	cnt = (int) (79.009-(99.994)-(59.05)-(42.886)-(85.132)-(33.192)-(tcb->m_ssThresh)-(57.025)-(15.053));
	segmentsAcked = (int) (66.153*(73.78)*(20.737));

}
if (m_cWndCnt > cnt) {   tcb->m_cWnd += tcb->m_segmentSize;   m_cWndCnt = 0; }
segmentsAcked = (int) (50.479-(49.04)-(0.273));

// generated


}

```


## EXAMPLE OF FIRST GENERATION INDIVIDUAL

run 1 individual 17
```c++
void
TcpBic::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);

// generated
float PkZiKXiiXePbUNbr = (float) (71.775-(46.148));
float QSQjvCRxWrcHoeAC = (float) (tcb->m_segmentSize+(segmentsAcked)+(75.677)+(28.769)+(93.423));
ReduceCwnd (tcb);
if (QSQjvCRxWrcHoeAC <= QSQjvCRxWrcHoeAC) {
	cnt = (int) (0.1/72.53);
	tcb->m_segmentSize = (int) ((82.14+(7.667)+(tcb->m_segmentSize)+(27.618)+(13.798)+(53.378))/79.286);
	PkZiKXiiXePbUNbr = (float) (tcb->m_segmentSize+(85.79)+(77.678)+(PkZiKXiiXePbUNbr));

} else {
	cnt = (int) (51.3-(65.764)-(84.702)-(50.841)-(20.607)-(14.528));
	tcb->m_cWnd = (int) (segmentsAcked-(21.269)-(cnt));

}
if (tcb->m_segmentSize >= PkZiKXiiXePbUNbr) {
	tcb->m_cWnd = (int) (((67.442)+((61.527+(24.607)+(62.571)+(39.909)))+((7.175*(83.61)*(cnt)*(67.248)*(70.391)*(39.44)*(5.921)*(84.752)*(61.851)))+(0.1)+(70.282))/((0.1)+(0.1)));
	cnt = (int) (19.757-(QSQjvCRxWrcHoeAC)-(73.24)-(23.041)-(2.81)-(tcb->m_segmentSize)-(70.686)-(6.057));

} else {
	tcb->m_cWnd = (int) (16.033-(8.206)-(tcb->m_ssThresh)-(47.106)-(QSQjvCRxWrcHoeAC)-(98.161)-(72.781)-(segmentsAcked)-(12.677));

}
// generated


}
```