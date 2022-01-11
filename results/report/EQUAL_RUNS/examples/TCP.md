## Examples of Baseline vs Best Individuals


### Baseline
Some functions are borrowed from TCP Linux Reno, but not used in the baseline, they are here to be used by generated code.
```c++
/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2015 Natale Patriciello <natale.patriciello@gmail.com>
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
#include "tcp-congestion-ops.h"
#include "ns3/log.h"
#include <cstdlib>

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("TcpCongestionOps");

NS_OBJECT_ENSURE_REGISTERED (TcpCongestionOps);

TypeId
TcpCongestionOps::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::TcpCongestionOps")
    .SetParent<Object> ()
    .SetGroupName ("Internet")
  ;
  return tid;
}

TcpCongestionOps::TcpCongestionOps () : Object ()
{
}

TcpCongestionOps::TcpCongestionOps (const TcpCongestionOps &other) : Object (other)
{
}

TcpCongestionOps::~TcpCongestionOps ()
{
}

void
TcpCongestionOps::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);
}

void
TcpCongestionOps::PktsAcked (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked,
                             const Time& rtt)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked << rtt);
}

void
TcpCongestionOps::CongestionStateSet (Ptr<TcpSocketState> tcb,
                                      const TcpSocketState::TcpCongState_t newState)
{
  NS_LOG_FUNCTION (this << tcb << newState);
}

void
TcpCongestionOps::CwndEvent (Ptr<TcpSocketState> tcb,
                             const TcpSocketState::TcpCAEvent_t event)
{
  NS_LOG_FUNCTION (this << tcb << event);
}

bool
TcpCongestionOps::HasCongControl () const
{
  return false;
}

void
TcpCongestionOps::CongControl (Ptr<TcpSocketState> tcb,
                               const TcpRateOps::TcpRateConnection &rc,
                               const TcpRateOps::TcpRateSample &rs)
{
  NS_LOG_FUNCTION (this << tcb);
  NS_UNUSED (rc);
  NS_UNUSED (rs);
}

// RENO

NS_OBJECT_ENSURE_REGISTERED (TcpNewReno);

TypeId
TcpNewReno::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::TcpNewReno")
    .SetParent<TcpCongestionOps> ()
    .SetGroupName ("Internet")
    .AddConstructor<TcpNewReno> ()
  ;
  return tid;
}

TcpNewReno::TcpNewReno (void) : TcpCongestionOps ()
{
  NS_LOG_FUNCTION (this);
}

TcpNewReno::TcpNewReno (const TcpNewReno& sock)
  : TcpCongestionOps (sock)
{
  NS_LOG_FUNCTION (this);
}

TcpNewReno::~TcpNewReno (void)
{
}

/**
 * \brief Tcp NewReno slow start algorithm
 *
 * Defined in RFC 5681 as
 *
 * > During slow start, a TCP increments cwnd by at most SMSS bytes for
 * > each ACK received that cumulatively acknowledges new data.  Slow
 * > start ends when cwnd exceeds ssthresh (or, optionally, when it
 * > reaches it, as noted above) or when congestion is observed.  While
 * > traditionally TCP implementations have increased cwnd by precisely
 * > SMSS bytes upon receipt of an ACK covering new data, we RECOMMEND
 * > that TCP implementations increase cwnd, per:
 * >
 * >    cwnd += min (N, SMSS)                      (2)
 * >
 * > where N is the number of previously unacknowledged bytes acknowledged
 * > in the incoming ACK.
 *
 * The ns-3 implementation respect the RFC definition. Linux does something
 * different:
 * \verbatim
u32 tcp_slow_start(struct tcp_sock *tp, u32 acked)
  {
    u32 cwnd = tp->snd_cwnd + acked;

    if (cwnd > tp->snd_ssthresh)
      cwnd = tp->snd_ssthresh + 1;
    acked -= cwnd - tp->snd_cwnd;
    tp->snd_cwnd = min(cwnd, tp->snd_cwnd_clamp);

    return acked;
  }
  \endverbatim
 *
 * As stated, we want to avoid the case when a cumulative ACK increases cWnd more
 * than a segment size, but we keep count of how many segments we have ignored,
 * and return them.
 *
 * \param tcb internal congestion state
 * \param segmentsAcked count of segments acked
 * \return the number of segments not considered for increasing the cWnd
 */
uint32_t
TcpNewReno::SlowStart (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);

  if (segmentsAcked >= 1)
    {
      tcb->m_cWnd += tcb->m_segmentSize;
      NS_LOG_INFO ("In SlowStart, updated to cwnd " << tcb->m_cWnd << " ssthresh " << tcb->m_ssThresh);
      return segmentsAcked - 1;
    }

  return 0;
}

/**
 * \brief NewReno congestion avoidance
 *
 * During congestion avoidance, cwnd is incremented by roughly 1 full-sized
 * segment per round-trip time (RTT).
 *
 * \param tcb internal congestion state
 * \param segmentsAcked count of segments acked
 */
void
TcpNewReno::CongestionAvoidance (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);

  if (segmentsAcked > 0)
    {
      double adder = static_cast<double> (tcb->m_segmentSize * tcb->m_segmentSize) / tcb->m_cWnd.Get ();
      adder = std::max (1.0, adder);
      tcb->m_cWnd += static_cast<uint32_t> (adder);
      NS_LOG_INFO ("In CongAvoid, updated to cwnd " << tcb->m_cWnd <<
                   " ssthresh " << tcb->m_ssThresh);
    }
}

void
TcpNewReno::TcpLinuxCongestionAvoidance (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);

  uint32_t w = tcb->m_cWnd / tcb->m_segmentSize;
  if (m_cWndCnt >= w)
    {
      m_cWndCnt = 0;
      tcb->m_cWnd += tcb->m_segmentSize;
    }

  m_cWndCnt += segmentsAcked;
  if (m_cWndCnt >= w)
    {
      uint32_t delta = m_cWndCnt / w;

      m_cWndCnt -= delta * w;
      tcb->m_cWnd += delta * tcb->m_segmentSize;
    }
}

/**
 * \brief Try to increase the cWnd following the NewReno specification
 *
 * \see SlowStart
 * \see CongestionAvoidance
 *
 * \param tcb internal congestion state
 * \param segmentsAcked count of segments acked
 */
void
TcpNewReno::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);
  if (tcb->m_cWnd < tcb->m_ssThresh)
    {
      segmentsAcked = SlowStart (tcb, segmentsAcked);
    }

  if (tcb->m_cWnd >= tcb->m_ssThresh)
    {
      CongestionAvoidance (tcb, segmentsAcked);
    }


  /* At this point, we could have segmentsAcked != 0. This because RFC says
   * that in slow start, we should increase cWnd by min (N, SMSS); if in
   * slow start we receive a cumulative ACK, it counts only for 1 SMSS of
   * increase, wasting the others.
   *
   * // Incorrect assert, I am sorry
   * NS_ASSERT (segmentsAcked == 0);
   */
}

std::string
TcpNewReno::GetName () const
{
  return "TcpNewReno";
}

uint32_t
TcpNewReno::GetSsThresh (Ptr<const TcpSocketState> state,
                         uint32_t bytesInFlight)
{
  NS_LOG_FUNCTION (this << state << bytesInFlight);

  return std::max (2 * state->m_segmentSize, bytesInFlight / 2);
}

void
TcpNewReno::ReduceCwnd (Ptr<TcpSocketState> tcb)
{
  NS_LOG_FUNCTION (this << tcb);

  tcb->m_cWnd = std::max (tcb->m_cWnd.Get () / 2, tcb->m_segmentSize);
}

Ptr<TcpCongestionOps>
TcpNewReno::Fork ()
{
  return CopyObject<TcpNewReno> (this);
}

} // namespace ns3

```

TCP `IncreaseWindow` is changed as follow:

```c++
void
TcpNewReno::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);
  // if (tcb->m_cWnd < tcb->m_ssThresh)
  //   {
  //     segmentsAcked = SlowStart (tcb, segmentsAcked);
  //   }

  // if (tcb->m_cWnd >= tcb->m_ssThresh)
  //   {
  //     CongestionAvoidance (tcb, segmentsAcked);
  //   }


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
TcpNewReno::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);
//generated
segmentsAcked = SlowStart (tcb, segmentsAcked);
float ZigqhttjQPZZqYqh = (float) 89.615;
ReduceCwnd (tcb);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
if (tcb->m_segmentSize < tcb->m_cWnd) {
	segmentsAcked = (int) (14.163*(1.548)*(90.037)*(31.269));

} else {
	segmentsAcked = (int) (95.874+(6.459)+(25.604)+(67.102)+(79.782)+(14.508)+(77.982));
	ZigqhttjQPZZqYqh = (float) (segmentsAcked+(57.471)+(54.386)+(segmentsAcked)+(16.029)+(89.55)+(70.284));
	segmentsAcked = SlowStart (tcb, segmentsAcked);

}
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
if (tcb->m_segmentSize < segmentsAcked) {
	ZigqhttjQPZZqYqh = (float) ((75.449+(ZigqhttjQPZZqYqh)+(53.448)+(86.699)+(tcb->m_ssThresh)+(segmentsAcked)+(28.415)+(tcb->m_cWnd))/0.1);

} else {
	ZigqhttjQPZZqYqh = (float) (99.266*(8.729)*(30.443)*(83.36)*(55.644)*(92.908)*(tcb->m_cWnd));

}
if (tcb->m_segmentSize < segmentsAcked) {
	ZigqhttjQPZZqYqh = (float) ((75.449+(ZigqhttjQPZZqYqh)+(53.448)+(86.699)+(tcb->m_ssThresh)+(segmentsAcked)+(28.415)+(tcb->m_cWnd))/0.1);

} else {
	ZigqhttjQPZZqYqh = (float) (99.266*(8.729)*(30.443)*(83.36)*(55.644)*(92.908)*(tcb->m_cWnd));

}
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
if (tcb->m_segmentSize < segmentsAcked) {
	ZigqhttjQPZZqYqh = (float) ((75.449+(ZigqhttjQPZZqYqh)+(53.448)+(86.699)+(tcb->m_ssThresh)+(segmentsAcked)+(28.415)+(tcb->m_cWnd))/0.1);

} else {
	ZigqhttjQPZZqYqh = (float) (99.266*(8.729)*(30.443)*(83.36)*(55.644)*(92.908)*(tcb->m_cWnd));

}
segmentsAcked = SlowStart (tcb, segmentsAcked);
ReduceCwnd (tcb);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
if (tcb->m_segmentSize < tcb->m_cWnd) {
	segmentsAcked = (int) (95.874+(6.459)+(25.604)+(67.102)+(79.782)+(14.508)+(77.982));
	ZigqhttjQPZZqYqh = (float) (segmentsAcked+(57.471)+(54.386)+(segmentsAcked)+(16.029)+(89.55)+(70.284));
	segmentsAcked = SlowStart (tcb, segmentsAcked);

} else {
	segmentsAcked = (int) (14.163*(1.548)*(90.037)*(31.269));

}
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
if (tcb->m_segmentSize < segmentsAcked) {
	ZigqhttjQPZZqYqh = (float) ((75.449+(ZigqhttjQPZZqYqh)+(53.448)+(86.699)+(tcb->m_ssThresh)+(segmentsAcked)+(28.415)+(tcb->m_cWnd))/0.1);

} else {
	ZigqhttjQPZZqYqh = (float) (99.266*(8.729)*(30.443)*(83.36)*(55.644)*(92.908)*(tcb->m_cWnd));

}
if (tcb->m_segmentSize < segmentsAcked) {
	ZigqhttjQPZZqYqh = (float) ((75.449+(ZigqhttjQPZZqYqh)+(53.448)+(86.699)+(tcb->m_ssThresh)+(segmentsAcked)+(28.415)+(tcb->m_cWnd))/0.1);

} else {
	ZigqhttjQPZZqYqh = (float) (99.266*(8.729)*(30.443)*(83.36)*(55.644)*(92.908)*(tcb->m_cWnd));

}
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
if (tcb->m_segmentSize < segmentsAcked) {
	ZigqhttjQPZZqYqh = (float) ((75.449+(ZigqhttjQPZZqYqh)+(53.448)+(86.699)+(tcb->m_ssThresh)+(segmentsAcked)+(28.415)+(tcb->m_cWnd))/0.1);

} else {
	ZigqhttjQPZZqYqh = (float) (99.266*(8.729)*(30.443)*(83.36)*(55.644)*(92.908)*(tcb->m_cWnd));

}
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
segmentsAcked = SlowStart (tcb, segmentsAcked);
//generated
}

```

run 2 gen 50 ind 29
```c++
void
TcpNewReno::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);
//generated
ReduceCwnd (tcb);
int QBvoLsqUfVDfLTMB = (int) (-42.35*(54.351)*(-25.138)*(78.661)*(-56.726)*(15.385)*(37.575));
tcb->m_cWnd = (int) (-48.194+(-22.458)+(-73.032));
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
tcb->m_cWnd = (int) (71.765+(74.349)+(67.252));
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
ReduceCwnd (tcb);
tcb->m_cWnd = (int) (61.346+(-15.976)+(-36.48));
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
ReduceCwnd (tcb);
CongestionAvoidance (tcb, segmentsAcked);
ReduceCwnd (tcb);
CongestionAvoidance (tcb, segmentsAcked);
tcb->m_cWnd = (int) (-32.983+(-58.025)+(-28.458));
CongestionAvoidance (tcb, segmentsAcked);
ReduceCwnd (tcb);
CongestionAvoidance (tcb, segmentsAcked);
tcb->m_cWnd = (int) (-53.048+(24.005)+(22.387));
CongestionAvoidance (tcb, segmentsAcked);
tcb->m_cWnd = (int) (83.353+(-8.097)+(61.572));
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
ReduceCwnd (tcb);
tcb->m_cWnd = (int) (-38.563+(93.847)+(64.136));
tcb->m_cWnd = (int) (3.139+(-1.95)+(-46.581));
CongestionAvoidance (tcb, segmentsAcked);
ReduceCwnd (tcb);
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
tcb->m_cWnd = (int) (-53.767+(-60.09)+(-24.775));
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
tcb->m_cWnd = (int) (56.808+(-23.365)+(1.508));
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
ReduceCwnd (tcb);
CongestionAvoidance (tcb, segmentsAcked);
ReduceCwnd (tcb);
CongestionAvoidance (tcb, segmentsAcked);
tcb->m_cWnd = (int) (-75.729+(94.303)+(4.895));
CongestionAvoidance (tcb, segmentsAcked);
tcb->m_cWnd = (int) (97.102+(-84.635)+(41.19));
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);
ReduceCwnd (tcb);
ReduceCwnd (tcb);
tcb->m_cWnd = (int) (18.157+(-87.81)+(37.68));
tcb->m_cWnd = (int) (37.435+(91.114)+(-72.979));
CongestionAvoidance (tcb, segmentsAcked);
CongestionAvoidance (tcb, segmentsAcked);

// generated


}

```


## EXAMPLE OF FIRST GENERATION INDIVIDUAL

run 1 individual 27
```c++
void
TcpNewReno::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);
//generated
if (segmentsAcked < tcb->m_segmentSize) {
	tcb->m_segmentSize = (int) (82.348*(94.944));

} else {
	tcb->m_segmentSize = (int) (98.233*(33.251)*(tcb->m_cWnd)*(47.871)*(25.399)*(51.385)*(43.954)*(tcb->m_cWnd)*(39.922));
	tcb->m_segmentSize = (int) (90.804-(segmentsAcked)-(43.903)-(65.132)-(64.573)-(54.878)-(tcb->m_segmentSize));
	TcpLinuxCongestionAvoidance (tcb, segmentsAcked);

}
if (tcb->m_ssThresh <= segmentsAcked) {
	tcb->m_cWnd = (int) (79.192+(50.391)+(52.786)+(segmentsAcked)+(17.68));

} else {
	tcb->m_cWnd = (int) (37.092+(73.493)+(tcb->m_segmentSize));
	tcb->m_segmentSize = (int) (31.352-(97.999)-(38.887)-(69.582)-(42.383)-(segmentsAcked)-(80.062)-(33.17)-(68.031));
	segmentsAcked = (int) (12.323-(3.443)-(38.319)-(49.427)-(54.044)-(tcb->m_ssThresh)-(61.407)-(tcb->m_segmentSize));

}
tcb->m_segmentSize = (int) (segmentsAcked+(tcb->m_cWnd)+(71.994)+(0.943)+(0.682)+(segmentsAcked)+(81.494)+(26.663)+(75.758));
float kYdivCgKONQSapeP = (float) (63.422+(tcb->m_cWnd)+(10.568)+(69.823)+(72.905)+(88.032)+(41.018)+(13.469)+(22.079));
if (tcb->m_ssThresh == tcb->m_cWnd) {
	tcb->m_cWnd = (int) (tcb->m_cWnd*(17.497)*(segmentsAcked)*(33.198)*(28.422)*(78.11)*(35.358)*(25.216));
	tcb->m_ssThresh = (int) (85.345*(38.941)*(92.741)*(85.88)*(10.415)*(64.5)*(45.542));

} else {
	tcb->m_cWnd = (int) (27.67+(22.391)+(segmentsAcked)+(73.775)+(20.496)+(89.977));
	segmentsAcked = SlowStart (tcb, segmentsAcked);
	segmentsAcked = (int) (58.72-(69.411)-(kYdivCgKONQSapeP)-(93.713));

}
if (tcb->m_ssThresh == tcb->m_segmentSize) {
	segmentsAcked = (int) (52.706+(12.611)+(tcb->m_cWnd)+(10.64));
	segmentsAcked = (int) (kYdivCgKONQSapeP-(70.749)-(15.995)-(tcb->m_ssThresh)-(30.693)-(tcb->m_cWnd)-(68.254)-(30.092));
	tcb->m_cWnd = (int) ((22.123+(94.456)+(23.248))/15.525);

} else {
	segmentsAcked = (int) (31.932*(20.693)*(17.48)*(50.046)*(49.112));

}
segmentsAcked = SlowStart (tcb, segmentsAcked);
tcb->m_segmentSize = (int) (73.983*(tcb->m_segmentSize)*(13.204)*(45.156)*(56.712)*(96.904)*(60.733)*(42.372));

// generated


}
```