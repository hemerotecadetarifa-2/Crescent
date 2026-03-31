#!/usr/bin/env python3
"""
CRESCENT MOON VISIBILITY (v.1)
By Wenceslao Segura, 2024, wenceslaotarifa@gmail.com
Python port of the original KBS (BASIC) software.

Determines the visibility of the lunar crescent after new moon,
including Islamic month start predictions.
"""

import math
import sys

PI = math.pi


# ---------------------------------------------------------------------------
# Astronomical helper functions
# ---------------------------------------------------------------------------

def julian_day(yea, mont, da, hou=0, minu=0, seco=0):
    """Return (JD, JD0, T0, T) for a Gregorian/Julian calendar date."""
    da1 = da - 1
    mont1 = (mont + 9) % 12
    yea1 = yea + 4716 - int((14 - mont) / 12)

    s = -int(3 * (1 + int((yea1 - 6316) / 100)) / 4) - 10
    jd1 = int(1461 * yea1 / 4) + int((153 * mont1 + 2) / 5) + da1 - 1401.5 + s

    if jd1 < 2299160.5:
        jd1 -= s

    t0 = (jd1 - 2451545) / 36525

    jd = int(1461 * yea1 / 4) + int((153 * mont1 + 2) / 5) + da1 - 1401.5 + s + (hou + (minu + seco / 60) / 60) / 24
    if jd < 2299160.5:
        jd -= s

    t = (jd - 2451545) / 36525
    return jd, jd1, t0, t


def reverse_julian_day(jd):
    """Return (yea, mont, da, hou, minu, seco) from a Julian day."""
    s = int(3 * (1 + int((4 * jd - 9222033) / 146097)) / 4) + 10
    jd_adj = jd
    if jd > 2299160.5:
        jd_adj = jd + s
    j1 = int(jd_adj + 0.5) + 1401
    yea1 = int((4 * j1 + 3) / 1461)
    tt = int(((4 * j1 + 3) % 1461) / 4)
    mont1 = int((5 * tt + 2) / 153)
    da1 = int(((5 * tt + 2) % 153) / 5)
    tt1 = jd - 0.5 - int(jd - 0.5)
    hou = int(24 * tt1)
    minu = int(60 * (24 * tt1 - hou))
    seco = math.ceil(60 * (60 * (24 * tt1 - hou) - minu))
    da = da1 + 1
    mont = (mont1 + 2) % 12 + 1
    yea = yea1 - 4716 + int((14 - mont) / 12)
    return yea, mont, da, hou, minu, seco


def delta_t(jd3):
    """Difference between Terrestrial Time and Universal Time (in days)."""
    t3 = (jd3 - 2451545) / 36525
    return (80.4 + 111.6 * t3 + 31 * t3 ** 2) / (3600 * 24)


def longitude_sun(jd):
    """Apparent ecliptic longitude, right ascension and declination of the Sun.

    Returns (LS_deg, alfaS_rad, deltaS_rad, epsilon_deg).
    """
    t = (jd - 2451545) / 36525

    ls0 = 280.46645 + 36000.76983 * t + 0.0003032 * t ** 2
    ls0 = (ls0 / 360 - int(ls0 / 360)) * 360
    if ls0 < 0:
        ls0 += 360

    as0 = 357.52910 + 35999.05030 * t - 0.0001559 * t ** 2 - 0.00000048 * t ** 3
    as0 = (as0 / 360 - int(as0 / 360)) * 360
    if as0 < 0:
        as0 += 360

    _es = 0.016708617 - 0.000042037 * t - 0.0000001236 * t ** 2

    cs = ((1.914600 - 0.004817 * t - 0.000014 * t ** 2) * math.sin(as0 * PI / 180)
          + (0.019993 - 0.000101 * t) * math.sin(2 * as0 * PI / 180)
          + 0.000290 * math.sin(3 * as0 * PI / 180))

    ls = ls0 + cs - 0.00569 - 0.00478 * math.sin((125.04 - 1934.136 * t) * PI / 180)

    epsilon = 23.43929111 - 0.01300417 * t - 0.00000016388 * t ** 2

    tan_alfa = math.cos(epsilon * PI / 180) * math.sin(ls * PI / 180) / math.cos(ls * PI / 180)
    alfa_s = math.atan(tan_alfa)
    cos_ls = math.cos(ls * PI / 180)
    sin_ls = math.sin(ls * PI / 180)
    if cos_ls < 0 and sin_ls < 0:
        alfa_s += PI
    if cos_ls < 0 and sin_ls > 0:
        alfa_s += PI
    if alfa_s < 0:
        alfa_s += 2 * PI

    sin_delta = math.sin(epsilon * PI / 180) * math.sin(ls * PI / 180)
    delta_s = math.asin(sin_delta)

    return ls, alfa_s, delta_s, epsilon


def coordinate_sun(jd, long_rad, fi):
    """Horizontal coordinates of the Sun.

    Returns (AzS, hS0, hST, RS, alfaS, deltaS).
    """
    jd2 = jd
    t = (jd - 2451545) / 36525

    ls0 = 280.46645 + 36000.76983 * t + 0.0003032 * t ** 2
    ls0 = (ls0 / 360 - int(ls0 / 360)) * 360
    if ls0 < 0:
        ls0 += 360

    as0 = 357.52910 + 35999.05030 * t - 0.0001559 * t ** 2 - 0.00000048 * t ** 3
    as0 = (as0 / 360 - int(as0 / 360)) * 360
    if as0 < 0:
        as0 += 360

    es = 0.016708617 - 0.000042037 * t - 0.0000001236 * t ** 2

    cs = ((1.914600 - 0.004817 * t - 0.000014 * t ** 2) * math.sin(as0 * PI / 180)
          + (0.019993 - 0.000101 * t) * math.sin(2 * as0 * PI / 180)
          + 0.000290 * math.sin(3 * as0 * PI / 180))

    ls = ls0 + cs - 0.00569 - 0.00478 * math.sin((125.04 - 1934.136 * t) * PI / 180)

    epsilon = 23.43929111 - 0.01300417 * t - 0.00000016388 * t ** 3

    tan_alfa = math.cos(epsilon * PI / 180) * math.sin(ls * PI / 180) / math.cos(ls * PI / 180)
    alfa_s = math.atan(tan_alfa)
    cos_ls = math.cos(ls * PI / 180)
    sin_ls = math.sin(ls * PI / 180)
    if cos_ls < 0 and sin_ls < 0:
        alfa_s += PI
    if cos_ls < 0 and sin_ls > 0:
        alfa_s += PI
    if alfa_s < 0:
        alfa_s += 2 * PI

    sin_delta = math.sin(epsilon * PI / 180) * math.sin(ls * PI / 180)
    delta_s = math.asin(sin_delta)

    # Sidereal time
    yea, mont, da, hou, minu, seco = reverse_julian_day(jd)
    jd0, _, t0_val, _ = julian_day(yea, mont, da, 0, 0, 0)
    t0 = (jd0 - 2451545) / 36525
    ts0 = 6.697374558 + 2400.051337 * t0 + 0.000025863 * t0 ** 2
    ts0 = (ts0 / 24 - int(ts0 / 24)) * 24
    ts = ts0 + (jd2 - jd0) * 24 * 1.00273790935
    ts = (ts / 24 - int(ts / 24)) * 24

    # Hour angle
    hs = PI * ts / 12 - long_rad - alfa_s
    if hs < 0:
        hs += 2 * PI
    hs = (hs / (2 * PI) - int(hs / (2 * PI))) * 2 * PI

    # Geocentric altitude
    sin_h = math.sin(fi) * math.sin(delta_s) + math.cos(fi) * math.cos(delta_s) * math.cos(hs)
    h_s0 = math.asin(sin_h)

    # Azimuth
    cos_az = (-math.sin(delta_s) + math.sin(fi) * math.sin(h_s0)) / (math.cos(fi) * math.cos(h_s0))
    if hs > PI:
        cos_az = -cos_az
    cos_az = max(-1.0, min(1.0, cos_az))
    az_s = math.acos(cos_az)
    if hs > PI:
        az_s += PI

    h_st = h_s0  # ignoring Sun parallax

    rs = 1.000001018 * (1 - es ** 2) / (1 + es * math.cos((as0 + cs) * PI / 180)) * 149597870.71

    return az_s, h_s0, h_st, rs, alfa_s, delta_s


def coordinate_moon(jd, long_rad, fi):
    """Topocentric horizontal coordinates of the Moon.

    Returns (AzM, hM0, hMT, RM, alfaM, deltaM, parallax).
    """
    jd3 = jd
    dt = delta_t(jd3)
    jd_tt = jd + dt
    t = (jd_tt - 2451545) / 36525
    # restore jd to UT
    # (jd stays as UT for sidereal time below)

    lm0 = 218.3164591 + 481267.88134236 * t - 0.0013268 * t ** 2 + t ** 3 / 538841 - t ** 4 / 65194000
    dm = 297.8502042 + 445267.1115168 * t - 0.00163 * t ** 2 + t ** 3 / 545868 - t ** 4 / 113065000
    ms = 357.5291092 + 35999.0502909 * t - 0.0001536 * t ** 2 + t ** 3 / 24490000
    mm = 134.9634114 + 477198.8676313 * t + 0.008997 * t ** 2 + t ** 3 / 69699 - t ** 4 / 14712000
    fm = 93.2720993 + 483202.0175273 * t - 0.0034029 * t ** 2 - t ** 3 / 3526000 + t ** 4 / 863310000

    a1 = 119.75 + 131.849 * t
    a2 = 53.09 + 479264.29 * t
    a3 = 313.45 + 481266.484 * t
    ee = 1 - 0.002516 * t - 0.0000074 * t ** 2

    def s(deg):
        return math.sin(deg * PI / 180)

    def c(deg):
        return math.cos(deg * PI / 180)

    # Ecliptic longitude terms
    term_lm = (6288774 * s(mm) + 1274027 * s(2 * dm - mm) + 658314 * s(2 * dm)
               + 213618 * s(2 * mm) - 185116 * ee * s(ms) - 114332 * s(2 * fm)
               + 58793 * s(2 * dm - 2 * mm) + 57066 * ee * s(2 * dm - ms - mm)
               + 53322 * s(2 * dm + mm) + 45758 * ee * s(2 * dm - ms)
               - 40923 * ee * s(ms - mm) - 34720 * s(dm) - 30383 * ee * s(ms + mm)
               + 15327 * s(2 * dm - 2 * fm) - 12528 * s(mm + 2 * fm)
               + 10980 * s(mm - 2 * fm) + 10675 * s(4 * dm - mm) + 10034 * s(3 * mm)
               + 8548 * s(4 * dm - 2 * mm) - 7888 * ee * s(2 * dm + ms - mm)
               - 6766 * ee * s(2 * dm + ms) - 5163 * s(dm - mm)
               + 4987 * ee * s(dm + ms) + 4036 * ee * s(2 * dm - ms + mm)
               + 3994 * s(2 * dm + 2 * mm) + 3861 * s(4 * dm)
               + 3665 * s(2 * dm - 3 * mm) - 2689 * ee * s(ms - 2 * mm)
               - 2602 * s(2 * dm - mm + 2 * fm) + 2390 * ee * s(2 * dm - ms - 2 * mm)
               - 2348 * s(dm + mm) + 2236 * ee ** 2 * s(2 * dm - 2 * ms)
               - 2120 * ee * s(ms + 2 * mm) - 2069 * ee ** 2 * s(2 * ms)
               + 2048 * ee ** 2 * s(2 * dm - 2 * ms - mm) - 1773 * s(2 * dm + mm - 2 * fm)
               - 1595 * s(2 * dm + 2 * fm) + 1215 * ee * s(4 * dm - ms - mm)
               - 1110 * s(2 * mm + 2 * fm) - 892 * s(3 * dm - mm)
               - 810 * ee * s(2 * dm + ms + mm) + 759 * ee * s(4 * dm - ms - 2 * mm)
               - 713 * ee ** 2 * s(2 * ms - mm) - 700 * ee ** 2 * s(2 * dm + 2 * ms - mm)
               + 691 * ee * s(2 * dm + ms - 2 * mm) + 596 * ee * s(2 * dm - ms - 2 * fm)
               + 549 * s(4 * dm + mm) + 537 * s(4 * mm) + 520 * ee * s(4 * dm - ms)
               - 487 * s(dm - 2 * mm) - 399 * ee * s(2 * dm + ms - 2 * fm)
               - 381 * s(2 * mm - 2 * fm) + 351 * ee * s(dm + ms + mm)
               - 340 * s(3 * dm - 2 * mm) + 330 * s(4 * dm - 3 * mm)
               + 327 * ee * s(2 * dm - ms + 2 * mm) - 323 * ee ** 2 * s(2 * ms + mm)
               + 299 * ee * s(dm + ms - mm))

    term_lm += (3958 * s(a1) + 1962 * s(lm0 - fm) + 318 * s(a2))

    # Equation of the equinoxes
    ex = (-0.0047778 * s(125.04436 - 1934.13618 * t + 0.0020761 * t ** 2)
          - 0.000366667 * s(2 * (280.46645 + 36000.76982 * t + 0.0003037 * t ** 2)))

    lm = lm0 + term_lm / 1000000 + ex
    lm = (lm / 360 - int(lm / 360)) * 360
    if lm < 0:
        lm += 360

    # Ecliptic latitude terms
    term_bm = (5128122 * s(fm) + 280602 * s(mm + fm) + 277693 * s(mm - fm)
               + 173237 * s(2 * dm - fm) + 55413 * s(2 * dm - mm + fm)
               + 46271 * s(2 * dm - mm - fm) + 32573 * s(2 * dm + fm)
               + 17198 * s(2 * mm + fm) + 9266 * s(2 * dm + mm - fm)
               + 8822 * s(2 * mm - fm) + 8216 * ee * s(2 * dm - ms - fm)
               + 4324 * s(2 * dm - 2 * mm - fm) + 4200 * s(2 * dm + mm + fm)
               - 3359 * ee * s(2 * dm + ms - fm) + 2463 * ee * s(2 * dm - ms - mm + fm)
               + 2211 * ee * s(2 * dm - ms + fm) + 2065 * ee * s(2 * dm - ms - mm - fm)
               - 1870 * ee * s(ms - mm - fm) + 1828 * s(4 * dm - mm - fm)
               - 1794 * s(3 * fm) - 1794 * ee * s(ms + fm)
               - 1565 * ee * s(ms - mm + fm) - 1491 * s(dm + fm)
               - 1475 * ee * s(ms + mm + fm) - 1410 * ee * s(ms + mm - fm)
               - 1344 * ee * s(ms - fm) - 1335 * s(dm - fm)
               + 1107 * s(3 * mm + fm) + 1021 * s(4 * dm - fm)
               + 833 * s(4 * dm - mm + fm) + 777 * s(mm - 3 * fm)
               + 671 * s(4 * dm - 2 * mm + fm) + 607 * s(2 * dm - 3 * fm)
               + 596 * s(2 * dm + 2 * mm - fm) + 491 * ee * s(2 * dm - ms + mm - fm)
               - 451 * s(2 * dm - 2 * mm + fm) + 439 * s(3 * mm - fm)
               + 422 * s(2 * dm + 2 * mm + fm) + 421 * s(2 * dm - 3 * mm - fm)
               - 366 * ee * s(2 * dm + ms - mm + fm) - 351 * ee * s(2 * dm + ms + fm)
               + 331 * s(4 * dm + fm) + 315 * ee * s(2 * dm - ms + mm + fm)
               + 302 * ee ** 2 * c(2 * dm - 2 * ms - fm)
               - 283 * c(mm + 3 * fm)
               - 229 * ee * c(2 * dm + ms + mm - fm)
               + 223 * ee * c(dm + ms - fm) + 223 * ee * c(dm + ms + fm)
               - 220 * ee * c(ms - 2 * mm - fm)
               - 220 * ee * c(2 * dm + ms - mm - fm) - 185 * c(dm + mm + fm)
               + 181 * ee * c(2 * dm - ms - 2 * mm - fm)
               - 177 * ee * c(ms + 2 * mm + fm) + 176 * c(4 * dm - 2 * mm - fm)
               + 166 * ee * c(4 * dm - ms - mm - fm) - 164 * c(dm + mm - fm)
               + 132 * c(4 * dm + mm - fm) - 119 * c(dm - mm - fm)
               + 115 * ee * c(4 * dm - ms - fm) + 107 * ee ** 2 * c(2 * dm - 2 * ms + fm))

    term_bm += (-2235 * s(lm0) + 382 * s(a3) + 175 * s(a1 - fm)
                + 175 * s(a1 + fm) + 127 * s(lm0 - mm) - 115 * s(lm0 + mm))

    bm = term_bm / 1000000
    bm = (bm / 360 - int(bm / 360)) * 360

    # Obliquity
    epsilon = (23.43929167 - 0.01300277778 * t
               + 0.002555556 * c(125.04436 - 1934.13618 * t + 0.0020761 * t ** 2))

    # Geocentric declination
    sin_delta_m = (math.sin(bm * PI / 180) * math.cos(epsilon * PI / 180)
                   + math.cos(bm * PI / 180) * math.sin(epsilon * PI / 180) * math.sin(lm * PI / 180))
    delta_m = math.asin(max(-1.0, min(1.0, sin_delta_m)))

    # Geocentric right ascension
    tan_alfa_m = ((-math.tan(bm * PI / 180) * math.sin(epsilon * PI / 180)
                   + math.cos(epsilon * PI / 180) * math.sin(lm * PI / 180))
                  / math.cos(lm * PI / 180))
    alfa_m = math.atan(tan_alfa_m)
    if math.cos(lm * PI / 180) < 0:
        alfa_m += PI
    if alfa_m < 0:
        alfa_m += 2 * PI

    # Earth-Moon distance
    term_rm = (-20905355 * c(mm) - 3699111 * c(2 * dm - mm) - 2955968 * c(2 * dm)
               - 569925 * c(2 * mm) + 48888 * ee * c(ms) - 3149 * c(2 * fm)
               + 246158 * c(2 * dm - 2 * mm) - 152138 * ee * c(2 * dm - ms - mm)
               - 170733 * c(2 * dm + mm) - 204586 * ee * c(2 * dm - ms)
               - 129620 * ee * c(ms - mm) + 108743 * c(dm)
               + 104755 * ee * c(ms + mm) + 10321 * c(2 * dm - 2 * fm)
               + 79661 * c(mm - 2 * fm) - 34782 * c(4 * dm - mm)
               - 23210 * c(3 * mm) - 21636 * c(4 * dm - 2 * mm)
               + 24208 * ee * c(2 * dm + ms - mm) + 30824 * ee * c(2 * dm + ms)
               - 8379 * c(dm - mm) - 16675 * ee * c(dm + ms)
               - 12831 * ee * c(2 * dm - ms + mm) - 10445 * c(2 * dm + mm)
               - 11650 * c(4 * dm) + 14403 * c(2 * dm - 3 * mm)
               - 7003 * ee * c(ms - 2 * mm) + 10056 * ee * c(2 * dm - ms - 2 * mm)
               + 6322 * c(dm + mm) - 9884 * ee ** 2 * c(2 * dm - 2 * ms)
               + 5751 * ee * c(ms + 2 * mm) - 4950 * ee ** 2 * c(2 * dm - 2 * ms - mm)
               + 4130 * c(2 * dm + mm - 2 * fm) - 3958 * ee * c(4 * dm - ms - mm)
               + 3258 * c(3 * dm - mm) + 2616 * ee * c(2 * dm + ms + mm)
               - 1897 * ee * c(4 * dm - ms - 2 * mm) - 2117 * ee ** 2 * c(2 * ms - mm)
               + 2354 * ee ** 2 * c(2 * dm + 2 * ms - mm) - 1423 * c(4 * dm + mm)
               - 1117 * c(4 * mm) - 1571 * ee * c(4 * dm - ms)
               - 1739 * c(dm - 2 * mm) - 4421 * c(2 * mm - 2 * fm)
               + 1165 * ee ** 2 * c(2 * ms + mm) + 8752 * c(2 * dm - mm - 2 * fm))

    rm = 385000.56 + term_rm / 1000

    parallax = math.asin(6378.14 / rm)

    # Sidereal time
    frac = jd - int(jd)
    if frac > 0.5:
        jd0 = int(jd) + 0.5
    elif frac < 0.5:
        jd0 = int(jd) - 0.5
    else:
        jd0 = jd

    t0 = (jd0 - 2451545) / 36525
    ts0 = 6.697374558 + 2400.051337 * t0 + 0.000025863 * t0 ** 2
    ts = ts0 + (jd - jd0) * 24 * 1.00273790935
    ts = (ts / 24 - int(ts / 24)) * 24
    ts0 = (ts0 / 24 - int(ts0 / 24)) * 24

    # Hour angle
    hm = PI * ts / 12 - long_rad - alfa_m
    if hm < 0:
        hm += 2 * PI
    if hm < 0:
        hm += 2 * PI
    if hm >= 2 * PI:
        hm -= 2 * PI

    # Geocentric altitude
    sin_hm0 = math.sin(fi) * math.sin(delta_m) + math.cos(fi) * math.cos(delta_m) * math.cos(hm)
    hm0 = math.asin(sin_hm0)

    # Azimuth
    cos_az = (-math.sin(delta_m) + math.sin(fi) * math.sin(hm0)) / (math.cos(fi) * math.cos(hm0))
    if hm > PI:
        cos_az = -cos_az
    cos_az = max(-1.0, min(1.0, cos_az))
    az_m = math.acos(cos_az)
    if hm > PI:
        az_m += PI

    # Topocentric altitude
    tan_hmt = (math.sin(hm0) - math.sin(parallax)) / math.cos(hm0)
    hmt = math.atan(tan_hmt)

    return az_m, hm0, hmt, rm, alfa_m, delta_m, parallax


# ---------------------------------------------------------------------------
# True sunset / apparent sunset
# ---------------------------------------------------------------------------

def true_sunset(jd0, d, fi, long_rad):
    """Moment when the Sun is at depression d degrees below the horizon.

    Returns (JDTS, AzS).
    """
    t0 = (jd0 - 2451545) / 36525
    ts0 = 6.697374558 + 2400.051337 * t0 + 0.00002586305 * t0 ** 2
    ts0 = (ts0 / 24 - int(ts0 / 24)) * 24
    if ts0 < 0:
        ts0 += 24

    jd = jd0
    for _mm in range(4):
        _ls, alfa_s, delta_s, _eps = longitude_sun(jd)
        cos_hs = (math.sin(-d * PI / 180) - math.sin(fi) * math.sin(delta_s)) / (math.cos(fi) * math.cos(delta_s))
        cos_hs = max(-1.0, min(1.0, cos_hs))
        hs = math.acos(cos_hs)
        ts = (hs + long_rad + alfa_s) * 12 / PI
        sunset = ts - ts0
        if sunset > 24:
            sunset -= 24
        if sunset > 0:
            sunset -= 24
        sunset /= 1.00273790935
        if _mm < 3:
            jd = jd0 + sunset / 24

    jdts = jd0 + sunset / 24

    cos_az = (-math.sin(delta_s) - math.sin(fi) * math.sin(d * PI / 180)) / (math.cos(fi) * math.cos(d * PI / 180))
    cos_az = max(-1.0, min(1.0, cos_az))
    az_s = math.acos(cos_az)
    if hs > PI:
        az_s = -abs(az_s)

    return jdts, az_s


def apparent_sunset(ww, fi, long_rad, u4, u5, u6):
    """Apparent sunset (depression = -0.8333 deg). Returns JDAS."""
    for tt in range(2):
        jd0, _, _, _ = julian_day(int(u4[ww, 0]), int(u5[ww, 0]), int(u6[ww, 0]) + tt, 0, 0, 0)
        t0 = (jd0 - 2451545) / 36525
        ts0 = 6.697374558 + 2400.051337 * t0 + 0.00002586305 * t0 ** 2
        ts0 = (ts0 / 24 - int(ts0 / 24)) * 24
        if ts0 < 0:
            ts0 += 24

        jd = jd0
        for pp in range(3):
            _ls, alfa_s, delta_s, _eps = longitude_sun(jd)
            cos_hs = (math.sin(-0.83333 * PI / 180) - math.sin(fi) * math.sin(delta_s)) / (math.cos(fi) * math.cos(delta_s))
            cos_hs = max(-1.0, min(1.0, cos_hs))
            hs = math.acos(cos_hs)
            ts = (hs + long_rad + alfa_s) * 12 / PI
            app_sunset = ts - ts0
            if app_sunset > 24:
                app_sunset -= 24
            if app_sunset < 0:
                app_sunset += 24
            app_sunset /= 1.00273790935
            if pp < 2:
                jd = jd0 + app_sunset / 24

        jdas = jd0 + app_sunset / 24
        yea_check, _, da_check, _, _, _ = reverse_julian_day(jdas)
        if da_check >= u6[ww, 0]:
            return jdas
    return jdas


def moonset(jdas, long_rad, fi):
    """Apparent moonset. Returns (JDTM, hou, minu, seco, yea, mont, da)."""
    for uu in range(3):
        jd = jdas + uu
        for _ in range(24 * 60 * 2):  # max ~2 days of seconds
            az_m, hm0, hmt, rm, alfa_m, delta_m, par = coordinate_moon(jd, long_rad, fi)
            if hm0 <= 0.125 * PI / 180:
                yea, mont, da, hou, minu, seco = reverse_julian_day(jd)
                return jd, hou, minu, seco, yea, mont, da
            jd += 1.0 / (24 * 60 * 60)
    # fallback
    yea, mont, da, hou, minu, seco = reverse_julian_day(jd)
    return jd, hou, minu, seco, yea, mont, da


# ---------------------------------------------------------------------------
# Crescent centre, magnitude, luminance, threshold
# ---------------------------------------------------------------------------

def centre_crescent(hmt, hs0, az_m, az_s, rm, rs):
    """Position of the apparent centre of the crescent.

    Returns (ALT, FASET, hCA, dazimutC, width, hCT).
    """
    hm0_unused = hmt  # topocentric altitude already

    # Topocentric arc-light
    cos_alt = math.sin(hs0) * math.sin(hmt) + math.cos(hmt) * math.cos(hs0) * math.cos(az_m - az_s)
    cos_alt = max(-1.0, min(1.0, cos_alt))
    alt = math.acos(cos_alt)

    # Topocentric distance
    rmt = rm * math.cos(hmt) / max(math.cos(hmt), 1e-12)  # approximate

    # Topocentric phase angle
    denom = rmt / rs - math.cos(alt)
    tan_faset = math.sin(alt) / denom if abs(denom) > 1e-12 else 1e12
    faset = math.atan(tan_faset)
    sin_alt = math.sin(alt)
    cos_alt_v = math.cos(alt)
    ratio = rmt / rs - cos_alt_v
    if sin_alt > 0 and ratio > 0:
        faset = PI - faset
    elif sin_alt > 0 and ratio < 0:
        faset += PI
    elif sin_alt < 0 and ratio > 0:
        faset += 2 * PI
    elif sin_alt < 0 and ratio < 0:
        faset += PI

    # Crescent width (arc-seconds)
    width = 3600 * 1738 / rmt * (1 + math.cos(faset)) * 180 / PI

    # Position of the centre
    abs_hs0 = abs(hs0)
    tan_aux1 = (math.sin(alt) * math.sin(hmt)) / (math.cos(alt) * math.sin(hmt) + math.sin(abs_hs0))
    aux1 = math.atan(tan_aux1)
    radi = 1738 / rmt
    sin_hct = math.sin(hmt) * math.sin(aux1 - radi) / math.sin(aux1) if abs(math.sin(aux1)) > 1e-12 else 0
    sin_hct = max(-1.0, min(1.0, sin_hct))
    hct = math.asin(sin_hct)

    # Azimuth difference
    sign2 = 1
    diff = alt - aux1
    if abs(diff) < 1e-12:
        diff = 1e-12
    sin_aux2 = abs_hs0 / diff
    sin_aux2 = max(-1.0, min(1.0, sin_aux2))
    aux2 = math.asin(sin_aux2)
    tan_aux2 = math.tan(aux2) if abs(math.cos(aux2)) > 1e-12 else 1e12
    dazimut_c = abs(az_m - az_s) - (hmt - hct) / tan_aux2
    if az_m < az_s:
        sign2 = -1
    dazimut_c *= sign2

    # Apparent altitude (with refraction)
    aux3 = (10.3 * PI / 180) / (abs(hct) * 180 / PI + 5.11)
    hca = (1.02 * PI / (180 * 60)) / math.tan(abs(hct) + aux3) + hct

    return alt, faset, hca, dazimut_c, width, hct


def magnitude(faset, hca, he, hu, alfa_s, fi, dazimut, rm):
    """Lunar magnitude of the centre of the crescent.

    Returns (MAG, MAGAB, MAGABMa, MAGABmi, kg, ka, kaMax, kamin, ko, X).
    """
    fasetd = faset * 180 / PI

    # Lagrange interpolation for magnitude
    def lag(x, xi):
        prod = 1.0
        for xj in [150, 155, 160, 165, 170, 175]:
            if xj != xi:
                prod *= (x - xj) / (xi - xj)
        return prod

    mag_vals = [-3.58, -3.099, -2.519, -1.759, -0.689, 1.161]
    xi_vals = [150, 155, 160, 165, 170, 175]
    mag = sum(mv * lag(fasetd, xv) for mv, xv in zip(mag_vals, xi_vals))

    # Distance correction
    mag -= (2.5 / 2.302585) * math.log(385000 / rm)

    # Air mass
    z = PI / 2 - hca
    xg = 1.0 / (math.cos(z) + 0.01 * math.sqrt(8.2) * math.exp(-30 * math.cos(z) / math.sqrt(8.2)))
    xa = 1.0 / (math.cos(z) + 0.01 * math.sqrt(1.5) * math.exp(-30 * math.cos(z) / math.sqrt(1.5)))
    sin_z = math.sin(z)
    arg = 1 - (sin_z / (1 + 20 / 6378)) ** 2
    xo = arg ** (-0.5) if arg > 0 else 1e6

    _x = 1.0 / (math.cos(z) + 0.50572 * (6.07995 + 90 - z * 180 / PI) ** (-1.6364))

    # Attenuation coefficients
    kg = 0.1066 * math.exp(-he / 8.2)
    ko = 0.031 * (3 + 0.4 * (abs(fi) * math.cos(alfa_s) - math.cos(3 * abs(fi)))) / 3
    sign_val = 1 if fi >= 0 else -1
    log_hu = math.log(hu) if hu > 0 else 1e-6
    ka = 0.12 * math.exp(-he / 1.5) * (1 - 0.13897 / log_hu) ** (4 / 3) * (1 + 0.33 * sign_val * math.cos(alfa_s))
    ka_max = 0.25
    ka_min = 0.0

    magab = mag + kg * xg + ka * xa + ko * xo
    magab_ma = mag + kg * xg + ka_max * xa + ko * xo
    magab_mi = mag + kg * xg + ka_min * xa + ko * xo

    return mag, magab, magab_ma, magab_mi, kg, ka, ka_max, ka_min, ko, _x


def luminance_helwan(hs0_rad, hca_rad, dazimut_c_rad):
    """Logarithm of twilight sky luminance (Samaha, Asaad & Mikhail 1969).

    Returns LUMI (log cd/m^2).
    """
    d = abs(hs0_rad) * 180 / PI
    h = hca_rad * 180 / PI
    da = dazimut_c_rad * 180 / PI

    # B00 .. B250: luminance for various h at DA=0
    b00 = (3571 / 23760000 * d ** 4 - 1957 / 2376000 * d ** 3 - 11701 / 316800 * d ** 2
           - 10973 / 264000 * d + 343659 / 110000)
    b100 = (1459 / 4752000 * d ** 4 - 11633 / 2376000 * d ** 3 + 1873 / 528000 * d ** 2
            - 63577 / 264000 * d + 69341 / 22000)
    b200 = (6367 / 35640000 * d ** 4 - 5197 / 3564000 * d ** 3 - 19187 / 792000 * d ** 2
            - 75947 / 396000 * d + 20297 / 6875)
    b250 = (1937 / 23760000 * d ** 4 + 3121 / 2376000 * d ** 3 - 5173 / 105600 * d ** 2
            - 32443 / 264000 * d + 304973 / 110000)

    bh0 = (-(h - 10) / 10 * (h - 20) / 20 * (h - 25) / 25 * b00
           + h / 10 * (h - 20) / 10 * (h - 25) / 15 * b100
           - h / 20 * (h - 10) / 10 * (h - 25) / 5 * b200
           + h / 25 * (h - 10) / 15 * (h - 20) / 5 * b250)

    # DA=10
    b010 = (23 / 1814400 * d ** 5 - 601 / 1814400 * d ** 4 + 47179 / 9072000 * d ** 3
            - 7379 / 112000 * d ** 2 + 3349 / 504000 * d + 43111 / 14000)
    b1010 = (-4721 / 133056000 * d ** 5 + 854591 / 665280000 * d ** 4 - 367693 / 26611200 * d ** 3
             + 130877 / 4032000 * d ** 2 - 1905683 / 7392000 * d + 9560049 / 3080000)
    b2010 = (-6499 / 1995840000 * d ** 5 + 7697 / 79833600 * d ** 4 + 164117 / 79833600 * d ** 3
             - 217751 / 4032000 * d ** 2 - 14709817 / 110880000 * d + 72553 / 24640)
    b2510 = (49 / 31680000 * d ** 5 - 2371 / 31680000 * d ** 4 + 25741 / 6336000 * d ** 3
             - 33947 / 576000 * d ** 2 - 938599 / 5280000 * d + 1297873 / 440000)

    bh10 = (-(h - 10) / 10 * (h - 20) / 20 * (h - 25) / 25 * b010
            + h / 10 * (h - 20) / 10 * (h - 25) / 15 * b1010
            - h / 20 * (h - 10) / 10 * (h - 25) / 5 * b2010
            + h / 25 * (h - 10) / 15 * (h - 20) / 5 * b2510)

    # DA=20
    b020 = (-13843 / 221760000 * d ** 5 + 480233 / 221760000 * d ** 4 - 1067111 / 44352000 * d ** 3
            + 21151 / 268800 * d ** 2 - 10497947 / 36960000 * d + 9872341 / 3080000)
    b1020 = (-1271 / 83160000 * d ** 5 + 5381 / 10395000 * d ** 4 - 58453 / 16632000 * d ** 3
             - 551 / 21000 * d ** 2 - 35723 / 288750 * d + 1135737 / 385000)
    b2020 = (743 / 124740000 * d ** 5 - 38923 / 124740000 * d ** 4 + 211441 / 24948000 * d ** 3
             - 8147 / 84000 * d ** 2 - 117571 / 6930000 * d + 536071 / 192500)
    b2520 = (-347 / 55440000 * d ** 5 + 1901 / 18480000 * d ** 4 + 881 / 246400 * d ** 3
             - 71809 / 1008000 * d ** 2 - 853613 / 9240000 * d + 2126701 / 770000)

    bh20 = (-(h - 10) / 10 * (h - 20) / 20 * (h - 25) / 25 * b020
            + h / 10 * (h - 20) / 10 * (h - 25) / 15 * b1020
            - h / 20 * (h - 10) / 10 * (h - 25) / 5 * b2020
            + h / 25 * (h - 10) / 15 * (h - 20) / 5 * b2520)

    # DA=30
    b030 = (263 / 4435200 * d ** 5 - 47261 / 22176000 * d ** 4 + 647323 / 22176000 * d ** 3
            - 5179 / 26880 * d ** 2 + 298493 / 1232000 * d + 860327 / 308000)
    b1030 = (143789 / 1995840000 * d ** 5 - 4973191 / 1995840000 * d ** 4 + 2639141 / 79833600 * d ** 3
             - 852839 / 4032000 * d ** 2 + 25975847 / 110880000 * d + 8293237 / 3080000)
    b2030 = (48023 / 498960000 * d ** 5 - 1727707 / 498960000 * d ** 4 + 4748167 / 99792000 * d ** 3
             - 102001 / 336000 * d ** 2 + 11797859 / 27720000 * d + 1865519 / 770000)
    b2530 = (103253 / 997920000 * d ** 5 - 3691879 / 997920000 * d ** 4 + 10150753 / 199584000 * d ** 3
             - 655639 / 2016000 * d ** 2 + 26259719 / 55440000 * d + 3548613 / 1540000)

    bh30 = (-(h - 10) / 10 * (h - 20) / 20 * (h - 25) / 25 * b030
            + h / 10 * (h - 20) / 10 * (h - 25) / 15 * b1030
            - h / 20 * (h - 10) / 10 * (h - 25) / 5 * b2030
            + h / 25 * (h - 10) / 15 * (h - 20) / 5 * b2530)

    # Interpolate over DA
    lumi = (-(da - 10) / 10 * (da - 20) / 20 * (da - 30) / 30 * bh0
            + da / 10 * (da - 20) / 10 * (da - 30) / 20 * bh10
            - da / 20 * (da - 10) / 10 * (da - 30) / 10 * bh20
            + da / 30 * (da - 10) / 20 * (da - 20) / 10 * bh30)

    return lumi


def threshold(magab, magab_ma, magab_mi, lumi, prob):
    """Visibility coefficient of the lunar crescent.

    Returns (COEF, COEFMa, COEFmi, MAGTHRE).
    """
    magthre = 2.8337 - 1.250504175 * lumi - 0.14656945 * lumi ** 2

    # Correction for vision probability
    vico = (3487 / 3840000000000 * prob ** 5 - 139 / 640000000 * prob ** 4
            + 42557 / 1920000000 * prob ** 3 - 9729 / 8000000 * prob ** 2
            + 140951 / 3000000 * prob)
    if vico > 0:
        magthre -= 2.5 * math.log10(vico / 2)

    coef = int((magab - magthre) * 100) / 100
    coef_ma = magab_ma - magthre
    coef_mi = magab_mi - magthre
    return coef, coef_ma, coef_mi, magthre


# ---------------------------------------------------------------------------
# New moons
# ---------------------------------------------------------------------------

def compute_new_moons(yea):
    """Compute new moons for year yea. Returns list of (JD, yea, mont, da, hou, minu, seco)."""
    results = []
    k_start = math.ceil(12.3685 * (yea - 0.1 - 2000))
    k = k_start
    for i in range(16):
        t = k / 1236.85
        j = (2451550.09765 + 29.530588853 * k + 0.0001337 * t ** 2
             - 0.000000150 * t ** 3 + 0.00000000073 * t ** 4)
        e = 1 - 0.002516 * t - 0.0000074 * t ** 2
        m_val = (2.5534 + 29.10535669 * k - 0.0000218 * t ** 2 - 0.00000011 * t ** 3) * PI / 180
        m1 = (201.5643 + 385.81693528 * k + 0.0107438 * t ** 2 + 0.00001239 * t ** 3 - 0.000000058 * t ** 4) * PI / 180
        e1 = (160.7108 + 390.67050274 * k - 0.0016341 * t ** 2 - 0.00000227 * t ** 3 + 0.000000011 * t ** 2) * PI / 180
        o1 = (124.7746 - 1.5637558 * k + 0.0020691 * t ** 2 + 0.00000215 * t ** 3) * PI / 180

        s1 = (-0.4072 * math.sin(m1) + 0.17241 * e * math.sin(m_val)
              + 0.01608 * math.sin(2 * m1) + 0.01039 * math.sin(2 * e1)
              + 0.00739 * e * math.sin(m1 - m_val) - 0.00514 * e * math.sin(m1 + m_val)
              + 0.00208 * e ** 2 * math.sin(2 * m_val) - 0.00111 * math.sin(m1 - 2 * e1)
              - 0.00057 * math.sin(m1 + 2 * e1) + 0.00056 * e * math.sin(2 * m1 + m_val)
              - 0.00042 * math.sin(3 * m1) + 0.00042 * e * math.sin(m_val + 2 * e1)
              + 0.00038 * e * math.sin(m_val - 2 * e1) - 0.00024 * e * math.sin(2 * m1 - m_val)
              - 0.00017 * math.sin(o1)
              - 0.00007 * math.sin(m1 + 2 * m_val)
              + 0.00004 * math.sin(2 * m1 - 2 * e1)
              + 0.00004 * math.sin(3 * m_val)
              + 0.00003 * math.sin(m1 + m_val - 2 * e1)
              + 0.00003 * math.sin(2 * m1 + 2 * e1)
              - 0.00003 * math.sin(m1 + m_val + 2 * e1)
              + 0.00003 * math.sin(m1 - m_val + 2 * e1)
              - 0.00002 * math.sin(m1 - m_val - 2 * e1)
              - 0.00002 * math.sin(3 * m1 + m_val)
              + 0.00002 * math.sin(4 * m1))

        s2 = (0.000325 * math.sin((299.77 + 0.107408 * k - 0.009173 * t ** 2) * PI / 180)
              + 0.000165 * math.sin((251.88 + 0.016321 * k) * PI / 180)
              + 0.000164 * math.sin((251.83 + 26.651886 * k) * PI / 180)
              + 0.000126 * math.sin((349.42 + 36.412478 * k) * PI / 180)
              + 0.00011 * math.sin((84.66 + 18.206239 * k) * PI / 180)
              + 0.000062 * math.sin((141.74 + 53.303771 * k) * PI / 180)
              + 0.00006 * math.sin((207.14 + 2.453732 * k) * PI / 180)
              + 0.000056 * math.sin((154.84 + 7.306860 * k) * PI / 180)
              + 0.000047 * math.sin((34.52 + 27.261239 * k) * PI / 180)
              + 0.000042 * math.sin((207.19 + 0.121824 * k) * PI / 180)
              + 0.00004 * math.sin((291.34 + 1.844379 * k) * PI / 180)
              + 0.000037 * math.sin((161.72 + 24.198154 * k) * PI / 180)
              + 0.000035 * math.sin((239.56 + 25.513099 * k) * PI / 180)
              + 0.000023 * math.sin((331.55 + 3.592518 * k) * PI / 180))

        j += s1 + s2

        # Convert from TT to UT
        dt = delta_t(j)
        j -= dt
        y, mo, da, ho, mi, se = reverse_julian_day(j)
        if y == yea:
            results.append((j, y, mo, da, ho, mi, se, i))
        k += 1

    return results


# ---------------------------------------------------------------------------
# Islamic calendar
# ---------------------------------------------------------------------------

def islamic_month(jd):
    """Return Islamic month name from Julian day."""
    jd1 = jd + 7664 + 10
    y1 = int((30 * jd1 + 15) / 10631)
    t = int(((30 * jd1 + 15) % 10631) / 30)
    m1 = int(2 * t / 59)
    m = m1 % 12 + 1
    names = {
        1: "Muharram", 2: "Safar", 3: "Rabi I", 4: "Rabi II",
        5: "Jumanada I", 6: "Jumada II", 7: "Rajib", 8: "Shaban",
        9: "Ramadhan", 10: "Shawwal", 11: "Zul-Qida", 12: "Zul-Hijja"
    }
    return names.get(m, "?")


# ---------------------------------------------------------------------------
# Main visibility computation
# ---------------------------------------------------------------------------

class Matrix:
    """Simple 2D matrix with default 0."""
    def __init__(self):
        self._data = {}

    def __getitem__(self, key):
        return self._data.get(key, 0)

    def __setitem__(self, key, val):
        self._data[key] = val


def compute_visibility(long_rad, fi, yea_input, he, hu, prob, lunation_index):
    """Run the full crescent visibility computation.

    Parameters
    ----------
    long_rad : float   - geographic longitude in radians (positive westward)
    fi       : float   - latitude in radians
    yea_input: int     - year
    he       : float   - observer height in km
    hu       : float   - relative humidity (%)
    prob     : float   - vision probability (%)
    lunation_index: int - index into new-moon list for the year

    Returns dict with all results.
    """
    # Matrices
    C = Matrix(); HH = Matrix(); HH1 = Matrix(); HH2 = Matrix()
    U1 = Matrix(); U2 = Matrix(); U3 = Matrix()
    U4 = Matrix(); U5 = Matrix(); U6 = Matrix()
    U12 = Matrix(); U22 = Matrix(); U32 = Matrix()
    U42 = Matrix(); U52 = Matrix(); U62 = Matrix()
    R = Matrix(); R1 = Matrix(); R2 = Matrix()
    JDTSS = Matrix(); age = Matrix()
    FASETT = Matrix(); ALTT = Matrix()
    kk_m = Matrix(); kkMax_m = Matrix(); kkmin_m = Matrix()
    hCAA = Matrix(); hM00 = Matrix()
    dazimutt = {}; AzSS = Matrix(); AzMM = Matrix()
    widthh = Matrix()
    COEFmin_m = Matrix(); COEFMax_m = Matrix()

    U7 = {}; U8 = {}; U9 = {}
    U72 = {}; U82 = {}; U92 = {}
    MM1 = {}; MM2 = {}; MM3 = {}; MM4 = {}; MM5 = {}; MM6 = {}

    # New moons
    nm_list = compute_new_moons(yea_input)
    if lunation_index >= len(nm_list):
        print(f"  Lunation index {lunation_index} out of range (max {len(nm_list) - 1})")
        return None

    jdnm = nm_list[lunation_index][0]

    # Print header
    nm = nm_list[lunation_index]
    print()
    print("  ===CRESCENT MOON VISIBILITY TABLES===")
    print(f"  Longitude {int(long_rad * 180 / PI * 100) / 100} deg    "
          f"Latitude {int(fi * 180 / PI * 100) / 100} deg    "
          f"Height {he} km     Humidity {hu}%    Probability {prob}%")
    print(f"  New Moon date: {nm[1]}/{nm[2]}/{int(nm[3])}   {nm[4]}h {nm[5]}m {nm[6]}s")

    ww = 0
    info = 0

    while True:
        for w in range(131):
            d = w / 10.0
            jd_val = jdnm + ww
            yea_r, mont_r, da_r, _, _, _ = reverse_julian_day(jd_val)
            jd0, _, _, _ = julian_day(yea_r, mont_r, da_r, 0, 0, 0)

            jdts, az_s_sunset = true_sunset(jd0, d, fi, long_rad)

            JDTSS[ww, w] = jdts
            if JDTSS[ww, w] < JDTSS[ww, 0] and w > 0:
                jdts = JDTSS[ww, w] + 1

            # Recalculate JD0 for jdts
            yea_r2, mont_r2, da_r2, _, _, _ = reverse_julian_day(jdts)

            age[ww, w] = int(((jdts - jdnm) * 24 + 0.5) * 10) / 10

            # Date on prime meridian
            yea_u, mont_u, da_u, hou_u, minu_u, seco_u = reverse_julian_day(jdts)
            U1[ww, w] = hou_u; U2[ww, w] = minu_u; U3[ww, w] = seco_u
            U4[ww, w] = yea_u; U5[ww, w] = mont_u; U6[ww, w] = da_u

            # Local meridian date
            sign1 = 1 if long_rad >= 0 else -1
            jd_local = jdts - sign1 * int(((sign1 * long_rad * 180 / PI - 7.5) / 15) + 1) / 24
            yea_l, mont_l, da_l, hou_l, minu_l, seco_l = reverse_julian_day(jd_local)
            U12[ww, w] = hou_l; U22[ww, w] = minu_l; U32[ww, w] = seco_l
            U42[ww, w] = yea_l; U52[ww, w] = mont_l; U62[ww, w] = da_l

            # Sun coordinates at jdts
            az_s, hs0, hst, rs, alfa_s, delta_s = coordinate_sun(jdts, long_rad, fi)
            AzSS[ww, w] = az_s

            # Moon coordinates at jdts
            az_m, hm0, hmt, rm, alfa_m, delta_m, par = coordinate_moon(jdts, long_rad, fi)
            AzMM[ww, w] = az_m

            # Centre of crescent
            alt, faset, hca, dazimut_c, width_val, hct = centre_crescent(hmt, hs0, az_m, az_s, rm, rs)

            R[ww, w] = int(dazimut_c * 180 / PI * 10) / 10
            R1[ww, w] = int(R[ww, w])
            R2[ww, w] = abs(int((R[ww, w] - int(R[ww, w])) * 60 + 0.5))
            FASETT[ww, w] = faset
            ALTT[ww, w] = int(((alt * 180 / PI) + 0.05) * 10) / 10
            hCAA[ww, w] = hca
            if w == 0:
                dazimutt[ww] = int((180 * ((AzMM[ww, 0] - AzSS[ww, 0]) / PI) * 10 + 0.05)) / 10
            widthh[ww, w] = int(width_val + 0.5)
            hM00[ww, w] = int((hm0 * 180 / PI) * 10 + 0.05) / 10

            # Magnitude
            mag, magab, magab_ma, magab_mi, kg, ka, ka_max, ka_min, ko, x_val = magnitude(
                faset, hca, he, hu, alfa_s, fi, dazimut_c, rm)
            kk_m[ww, w] = int((kg + ka + ko + 0.005) * 100) / 100
            kkMax_m[ww, w] = int((kg + ka_max + ko + 0.005) * 100) / 100
            kkmin_m[ww, w] = int((kg + ka_min + ko + 0.005) * 100) / 100

            # Luminance
            lumi = luminance_helwan(hs0, hca, dazimut_c)

            # Threshold
            coef, coef_ma, coef_mi, magthre = threshold(magab, magab_ma, magab_mi, lumi, prob)

            HH[ww, w] = int(hCAA[ww, w] * 180 / PI * 100) / 100
            HH1[ww, w] = int(HH[ww, w])
            HH2[ww, w] = int((HH[ww, w] - int(HH[ww, w])) * 60 + 0.5)

            if hCAA[ww, w] <= 0:
                break

            COEFMax_m[ww, w] = coef_ma
            COEFmin_m[ww, w] = coef_mi
            C[ww, w] = coef
            if coef < 0:
                info = 1

        # --- Output for this day ---
        # Apparent sunset
        jdas = apparent_sunset(ww, fi, long_rad, U4, U5, U6)
        yea_as, mont_as, da_as, hou_as, minu_as, seco_as = reverse_julian_day(jdas)
        U7[ww] = hou_as; U8[ww] = minu_as; U9[ww] = seco_as
        U72[ww] = yea_as; U82[ww] = mont_as; U92[ww] = da_as

        # Moonset
        jdtm, hou_ms, minu_ms, seco_ms, yea_ms, mont_ms, da_ms = moonset(jdas, long_rad, fi)
        MM1[ww] = hou_ms; MM2[ww] = minu_ms; MM3[ww] = seco_ms
        lag_val = (jdtm - jdas) * 24 * 60
        if lag_val > 60 * 24:
            lag_val -= 24 * 60

        if JDTSS[ww, 0] >= jdnm - 0.5:
            print()
            print("  " + "-" * 100)
            print(f"  Date (prime meridian) {int(U4[ww, 0])}/{int(U5[ww, 0])}/{int(U6[ww, 0])}")
            print(f"  Topocentric phase angle: {int((FASETT[ww, 0] * 1800 + 0.05) / PI) / 10} deg"
                  f" - Topocentric light arc: {ALTT[ww, 0]} deg")
            print(f"  Attenuation coefficient (calc, max, min): {kk_m[ww, 0]} - {kkMax_m[ww, 0]} - {kkmin_m[ww, 0]}"
                  f"  Topocentric width: {widthh[ww, 0]}''")
            print(f"  True sunset (prime meridian): {int(U1[ww, 0])}:{int(U2[ww, 0])}:{int(U3[ww, 0])}"
                  f"  True alt Moon at sunset: {hM00[ww, 0]} deg"
                  f"  Azimuth diff at sunset: {dazimutt.get(ww, 0)} deg")
            print(f"  Apparent moonset: {MM1[ww]}:{MM2[ww]}:{MM3[ww]}"
                  f"  Apparent sunset: {U7[ww]}:{U8[ww]}:{U9[ww]}"
                  f"  Lag: {int(lag_val * 10 + 0.5) / 10} min")
            print("  If the visibility coefficient is negative or null the crescent is visible")
            print()
            print(f"  {'Sun dep':>8}  {'Vis coef':>8}  {'Alt':>8}  {'Time UT':>12}  {'Date PM':>12}  {'Az diff':>8}  {'Time local':>12}  {'Date local':>12}  {'Age(h)':>6}")
            print("  " + "-" * 100)

            for w_out in range(0, 131, 10):
                if HH[ww, 0] <= 0:
                    print("  Lunar crescent below the horizon. Invisible crescent")
                    break
                if HH[ww, w_out] <= 0:
                    break
                print(f"  {w_out / 10:8.1f}  {C[ww, w_out]:8.2f}  {HH1[ww, w_out]:3.0f}d{HH2[ww, w_out]:02.0f}'"
                      f"  {int(U1[ww, w_out]):02d}:{int(U2[ww, w_out]):02d}:{int(U3[ww, w_out]):02d}"
                      f"     {int(U4[ww, w_out])}/{int(U5[ww, w_out])}/{int(U6[ww, w_out])}"
                      f"    {int(R[ww, w_out] * 10 + 0.05) / 10:6.1f}d"
                      f"  {int(U12[ww, w_out]):02d}:{int(U22[ww, w_out]):02d}:{int(U32[ww, w_out]):02d}"
                      f"     {int(U42[ww, w_out])}/{int(U52[ww, w_out])}/{int(U62[ww, w_out])}"
                      f"  {age[ww, w_out]:6.1f}")

        ww += 1
        if info == 1:
            break

    top = ww - 1
    print("  " + "-" * 100)

    if FASETT[top, 0] != 0 and FASETT[top, 0] * 180 / PI < 150:
        print("  CAREFUL! The software is designed for phase angles greater than 150 deg")

    # --- Maximum visibility ---
    print()
    print("  ===INFORMATION ON MOON CRESCENT VISIBILITY===")
    il = 0
    w1 = 0
    for w in range(131):
        if C[top, w] < il:
            w1 = w
            il = C[top, w]

    print()
    print(f"  VISIBILITY FOR PROBABILITY {prob}%")
    print("  " + "-" * 30)
    yea_top, mont_top, da_top, _, _, _ = reverse_julian_day(jdnm + top)
    if il > -0.5 or il == -0.5:
        print(f"  Very difficult to see the crescent")
    elif -1 <= il < -0.5:
        print(f"  Difficult to see the crescent")
    elif -2 <= il < -1:
        print(f"  Likely to see the crescent")
    else:
        print(f"  Very likely to see the crescent")

    # First visibility
    w_first = 0
    for w in range(131):
        if C[top, w] < 0:
            w_first = w
            break

    print()
    print(f"  MOMENT OF FIRST VISIBILITY FOR PROBABILITY {prob}%")
    print("  " + "-" * 50)
    print(f"  Date (prime meridian):       {int(U4[top, w_first])}/{int(U5[top, w_first])}/{int(U6[top, w_first])}")
    print(f"  Date (observation meridian): {int(U42[top, w_first])}/{int(U52[top, w_first])}/{int(U62[top, w_first])}")
    print(f"  Sun depression:              {int(w_first / 10)}d {int((w_first / 10 - int(w_first / 10)) * 60 + 0.5)}'")
    print(f"  Altitude crescent centre:    {int(HH1[top, w_first])}d {int(HH2[top, w_first])}'")
    print(f"  Time (prime meridian):       {int(U1[top, w_first])}h {int(U2[top, w_first])}m {int(U3[top, w_first])}s")
    print(f"  Time (observation meridian): {int(U12[top, w_first])}h {int(U22[top, w_first])}m {int(U32[top, w_first])}s")
    print(f"  Azimuth difference:          {int(R1[top, w_first])}d {int(R2[top, w_first])}'")
    print(f"  Age of the Moon:             {age[top, w_first]} h")

    # Optimal visibility
    w = w1
    print()
    print(f"  MOMENT OF OPTIMAL VISIBILITY FOR PROBABILITY {prob}%")
    print("  " + "-" * 50)
    print(f"  Date (prime meridian):       {int(U4[top, w])}/{int(U5[top, w])}/{int(U6[top, w])}")
    print(f"  Date (observation meridian): {int(U42[top, w])}/{int(U52[top, w])}/{int(U62[top, w])}")
    print(f"  Sun depression:              {int(w / 10)}d {int((w / 10 - int(w / 10)) * 60 + 0.5)}'")
    print(f"  Altitude crescent centre:    {int(HH1[top, w])}d {int(HH2[top, w])}'")
    print(f"  Time (prime meridian):       {int(U1[top, w])}h {int(U2[top, w])}m {int(U3[top, w])}s")
    print(f"  Time (observation meridian): {int(U12[top, w])}h {int(U22[top, w])}m {int(U32[top, w])}s")
    print(f"  Azimuth difference:          {int(R1[top, w])}d {int(R2[top, w])}'")
    print(f"  Age of the Moon:             {age[top, w]} h")
    print(f"  Visibility coefficient:      {int((C[top, w] - 0.05) * 10) / 10}")

    # Islamic month
    print()
    print(f"  BEGINNING OF THE ISLAMIC MONTH FOR PROBABILITY {prob}%")
    print("  " + "-" * 50)
    yea_is = int(U42[top, w])
    mont_is = int(U52[top, w])
    da_is = int(U62[top, w])
    jd_is, _, _, _ = julian_day(yea_is, mont_is, da_is, 0, 0, 0)
    jd_is += 1
    mo_name = islamic_month(jd_is)
    yea_is2, mont_is2, da_is2, _, _, _ = reverse_julian_day(jd_is)
    print(f"  Beginning of Islamic month {mo_name} at longitude {int(long_rad * 180 / PI * 100) / 100} deg"
          f" and latitude {int(fi * 180 / PI * 100) / 100} deg"
          f" is {yea_is2}/{mont_is2}/{da_is2} (local time)")

    return {
    "top": top,
    "C": C,
    "HH": HH,
    "U1": U1,
    "U2": U2,
    "U3": U3,
    "U4": U4,
    "U5": U5,
    "U6": U6,
    "U12": U12,
    "U22": U22,
    "U32": U32,
    "U42": U42,
    "U52": U52,
    "U62": U62,
    "age": age
}


# ---------------------------------------------------------------------------
# Interactive entry
# ---------------------------------------------------------------------------

def get_input(prompt, type_fn=float, validate=None, error_msg=None):
    """Helper for validated input."""
    while True:
        try:
            val = type_fn(input(prompt))
            if validate and not validate(val):
                print(f"  {error_msg or 'Invalid input. Try again.'}")
                continue
            return val
        except (ValueError, EOFError):
            print("  Invalid input. Try again.")


def get_choice(prompt, options):
    """Helper for string choice input."""
    while True:
        val = input(prompt).strip().upper()
        if val in [o.upper() for o in options]:
            return val
        print("  Invalid choice. Try again.")


def main():
    print()
    print("  CRESCENT MOON VISIBILITY (v.1)")
    print("  By Wenceslao Segura, 2024 - Python port")
    print("  " + "=" * 60)

    while True:
        print()
        # Geographic longitude
        print("  Geographic longitude (-180 to 180 degrees)")
        lon_dir = get_choice("    East or West (E/W): ", ["E", "W"])
        dlong = get_input("    Degrees: ")
        mlong = get_input("    Minutes: ", default_val=0)
        slong = get_input("    Seconds: ", default_val=0) if True else 0
        long_deg = dlong + mlong / 60 + slong / 3600
        long_rad = long_deg * PI / 180
        if lon_dir == "E":
            long_rad = -long_rad
        if abs(long_rad) > PI:
            print("  Longitude must be between -180 and 180. Try again.")
            continue

        # Latitude
        print()
        print("  Geographic latitude (-60 to 60 degrees)")
        lat_dir = get_choice("    North or South (N/S): ", ["N", "S"])
        dfi = get_input("    Degrees: ")
        mfi = get_input("    Minutes: ", default_val=0)
        sfi = get_input("    Seconds: ", default_val=0) if True else 0
        fi = (dfi + mfi / 60 + sfi / 3600) * PI / 180
        if lat_dir == "S":
            fi = -fi
        if abs(fi) > 1.0472:
            print("  Latitude must be between -60 and 60. Try again.")
            continue

        # Year
        print()
        yea = get_input("  Year: ", int)

        # Height
        print()
        he = get_input("  Observer height (metres): ") / 1000  # convert to km

        # Humidity
        print()
        hu = get_input("  Relative humidity (>2%): ", validate=lambda x: x >= 2,
                       error_msg="Relative humidity must be >= 2%")

        # Probability
        print()
        prob = get_input("  Probability of seeing the crescent (0-100%, recommended 50%): ",
                         validate=lambda x: 0 <= x <= 100,
                         error_msg="Must be between 0 and 100")

        # Compute new moons
        print()
        nm_list = compute_new_moons(yea)
        print(f"  New Moons of the year {yea}:")
        print("  Units in Universal Time")
        print()
        for j, (jd_nm, y, mo, da, ho, mi, se, idx) in enumerate(nm_list):
            print(f"    {idx:2d}   Date: {y}/{mo}/{da}  {ho}h {mi}m {se}s")

        print()
        ss = get_input("  Lunation for which you want to know the visibility? ", int,
                       validate=lambda x: 0 <= x <= (nm_list[-1][7] if nm_list else 0),
                       error_msg="Invalid lunation index")

        # Find the entry with matching original index
        lunation_idx = None
        for i, entry in enumerate(nm_list):
            if entry[7] == ss:
                lunation_idx = i
                break
        if lunation_idx is None:
            print("  Lunation not found for this year.")
            continue

        compute_visibility(long_rad, fi, yea, he, hu, prob, lunation_idx)

        print()
        again = get_choice("  Do you want a new calculation? (Y/N): ", ["Y", "N"])
        if again == "N":
            print()
            print("  Thanks for using CRESCENT MOON VISIBILITY")
            print("  " + "=" * 45)
            break


def get_input(prompt, type_fn=float, validate=None, error_msg=None, default_val=None):
    """Helper for validated input."""
    while True:
        try:
            raw = input(prompt).strip()
            if raw == "" and default_val is not None:
                return default_val
            # Support comma as decimal separator
            raw = raw.replace(",", ".")
            val = type_fn(raw)
            if validate and not validate(val):
                print(f"  {error_msg or 'Invalid input. Try again.'}")
                continue
            return val
        except (ValueError, EOFError):
            print("  Invalid input. Try again.")


if __name__ == "__main__":
    main()
