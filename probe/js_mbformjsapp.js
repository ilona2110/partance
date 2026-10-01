!(function (t) {
  if ("object" == typeof exports && "undefined" != typeof module)
    module.exports = t();
  else if ("function" == typeof define && define.amd) define([], t);
  else {
    var e;
    (e =
      "undefined" != typeof window
        ? window
        : "undefined" != typeof global
        ? global
        : "undefined" != typeof self
        ? self
        : this),
      (e.MB_Form_JsApp = t());
  }
})(function () {
  var t, e, r;
  return (function e(t, r, n) {
    function s(o, a) {
      if (!r[o]) {
        if (!t[o]) {
          var u = "function" == typeof require && require;
          if (!a && u) return u(o, !0);
          if (i) return i(o, !0);
          var h = new Error("Cannot find module '" + o + "'");
          throw ((h.code = "MODULE_NOT_FOUND"), h);
        }
        var c = (r[o] = { exports: {} });
        t[o][0].call(
          c.exports,
          function (e) {
            var r = t[o][1][e];
            return s(r || e);
          },
          c,
          c.exports,
          e,
          t,
          r,
          n
        );
      }
      return r[o].exports;
    }
    for (
      var i = "function" == typeof require && require, o = 0;
      o < n.length;
      o++
    )
      s(n[o]);
    return s;
  })(
    {
      1: [
        function (t, e, r) {
          "use strict";
          function _classCallCheck(t, e) {
            if (!(t instanceof e))
              throw new TypeError("Cannot call a class as a function");
          }
          Object.defineProperty(r, "__esModule", { value: !0 });
          var n = (function () {
              function defineProperties(t, e) {
                for (var r = 0; r < e.length; r++) {
                  var n = e[r];
                  (n.enumerable = n.enumerable || !1),
                    (n.configurable = !0),
                    "value" in n && (n.writable = !0),
                    Object.defineProperty(t, n.key, n);
                }
              }
              return function (t, e, r) {
                return (
                  e && defineProperties(t.prototype, e),
                  r && defineProperties(t, r),
                  t
                );
              };
            })(),
            i = (function () {
              function MB_Form_JsApp() {
                _classCallCheck(this, MB_Form_JsApp),
                  (this.ContainerId = ""),
                  (this.AccountId = ""),
                  (this.OperationId = ""),
                  (this.UserId = ""),
                  (this.OperationType = ""),
                  (this.UserData = !0),
                  (this.UserDataCookie = !1),
                  (this.Debug = !1),
                  (this.Path = "https://public.message-business.com/"),
                  this.OnLoadStart,
                  this.OnLoadSuccess,
                  this.OnLoadError,
                  this.OnLoadEnd,
                  this.OnSubmitStart,
                  this.OnSubmitStartError,
                  this.OnSubmitSuccess,
                  this.OnSubmitError,
                  this.OnSubmitEnd,
                  this.OnSubmitRedirection,
                  this.OnSubmitDataSuccess,
                  this.OnSubmitDataError,
                  this.xhr,
                  this.url,
                  this.currentUrl,
                  this.container,
                  this.submitButton,
                  (this.asyncInProgress = !1);
              }
              return (
                n(MB_Form_JsApp, [
                  {
                    key: "Init",
                    value: function Init() {
                      1 == this.GetParameterByName("MBDEBUG") &&
                        (this.Debug = !0),
                        this.ShowDebug(
                          "Init 1 UserId=" +
                            this.UserId +
                            " this.UserData=" +
                            this.UserData +
                            " this.UserDataCookie=" +
                            this.UserDataCookie
                        ),
                        (void 0 !== this.UserId &&
                          null !== this.UserId &&
                          "" !== this.UserId) ||
                          (this.UserId = this.GetParameterByName("MBID")),
                        this.ShowDebug(
                          "Init 2 UserId=" +
                            this.UserId +
                            " this.UserData=" +
                            this.UserData +
                            " this.UserDataCookie=" +
                            this.UserDataCookie
                        ),
                        (void 0 !== this.UserId &&
                          null != this.UserId &&
                          "" != this.UserId) ||
                          (!0 === this.UserDataCookie &&
                            ((this.UserId = this.GetCookieValue(
                              "mb." + this.AccountId
                            )),
                            this.ShowDebug("UserDataCookie=" + this.UserId))),
                        "form" == this.OperationType
                          ? !0 === this.UserData &&
                            void 0 !== this.UserId &&
                            null != this.UserId &&
                            "" != this.UserId
                            ? (this.url =
                                this.Path +
                                "form/" +
                                this.AccountId +
                                "/" +
                                this.OperationId +
                                "/" +
                                this.UserId +
                                "/form.aspx?mbmode=ajax")
                            : (this.url =
                                this.Path +
                                "form/" +
                                this.AccountId +
                                "/" +
                                this.OperationId +
                                "/form.aspx?mbmode=ajax")
                          : !0 === this.UserData &&
                            void 0 !== this.UserId &&
                            null != this.UserId &&
                            "" != this.UserId
                          ? (this.url =
                              this.Path +
                              "survey/" +
                              this.AccountId +
                              "/" +
                              this.OperationId +
                              "/" +
                              this.UserId +
                              "/survey.aspx?mbmode=ajax")
                          : (this.url =
                              this.Path +
                              "survey/" +
                              this.AccountId +
                              "/" +
                              this.OperationId +
                              "/survey.aspx?mbmode=ajax");
                      var t = "",
                        e = this.GetParameters();
                      void 0 !== e &&
                        Array.isArray(e) &&
                        e.forEach(function (e) {
                          e.name.startsWith("form") &&
                            (t += "&" + e.name + "=" + e.value);
                        }),
                        (this.url += t),
                        (this.container = document.getElementById(
                          this.ContainerId
                        )),
                        this.Load();
                    },
                  },
                  {
                    key: "GetCookieValue",
                    value: function GetCookieValue(t) {
                      t += "=";
                      for (
                        var e = document.cookie.split(";"), r = 0;
                        r < e.length;
                        r++
                      ) {
                        for (var n = e[r]; " " == n.charAt(0); )
                          n = n.substring(1);
                        if (0 == n.indexOf(t))
                          return n.substring(t.length, n.length);
                      }
                      return "";
                    },
                  },
                  {
                    key: "Load",
                    value: function Load() {
                      var t = this;
                      this.ShowDebug("Load"),
                        this.ShowDebug("! OnLoadStart"),
                        "function" == typeof this.OnLoadStart &&
                          this.OnLoadStart(),
                        (this.xhr = this.GetXMLHttpRequest()),
                        (this.xhr.onreadystatechange = function () {
                          if (
                            4 != t.xhr.readyState ||
                            (200 != t.xhr.status && 0 != t.xhr.status)
                          )
                            t.xhr.status >= 400 &&
                              (t.ShowDebug("! OnLoadError " + t.xhr.status),
                              "function" == typeof t.OnLoadError &&
                                t.OnLoadError(),
                              t.ShowDebug("! OnLoadEnd"),
                              "function" == typeof t.OnLoadEnd &&
                                t.OnLoadEnd());
                          else {
                            t.container.innerHTML = t.xhr.responseText;
                            try {
                              t.InitSubmitButton(),
                                t.ShowError(),
                                t.ShowDebug("! OnLoadSuccess"),
                                "function" == typeof t.OnLoadSuccess &&
                                  t.OnLoadSuccess();
                            } catch (e) {
                              t.ShowDebug("! OnLoadError " + t.xhr.status),
                                "function" == typeof t.OnLoadError &&
                                  t.OnLoadError();
                            }
                            t.ShowDebug("! OnLoadEnd"),
                              "function" == typeof t.OnLoadEnd && t.OnLoadEnd();
                          }
                        }),
                        this.xhr.open("GET", this.url, !0),
                        this.xhr.send(null);
                    },
                  },
                  {
                    key: "ShowError",
                    value: function ShowError() {
                      this.ShowDebug("ShowError");
                      var t = document.getElementById("formErrorIds");
                      if (void 0 !== t && null != t) {
                        var e = t.value;
                        if (null != e && "" != e && "," != e)
                          for (var r = e.split(","), n = 0; n < r.length; n++)
                            null != r[n] &&
                              "" != r[n] &&
                              (document
                                .getElementById("labelOf-" + r[n])
                                .classList.add("formError"),
                              document
                                .getElementById(r[n])
                                .classList.add("formError"));
                      }
                    },
                  },
                  {
                    key: "Submit",
                    value: function Submit(t, e) {
                      var r = this,
                        n = !0;
                      if (
                        ("next" != e && "previous" != e && (e = "submit"),
                        this.ShowDebug("Submit"),
                        this.ShowDebug("! OnSubmitStart(" + e + ")"),
                        "function" == typeof r.OnSubmitStart &&
                          (n = r.OnSubmitStart(e)),
                        !1 === r.asyncInProgress)
                      )
                        if (((r.asyncInProgress = !0), !0 === n)) {
                          var i = this.container.getElementsByTagName(
                              "form"
                            )[0],
                            s = new FormData(i);
                          (this.xhr = this.GetXMLHttpRequest()),
                            (this.xhr.onreadystatechange = function () {
                              if (
                                4 != r.xhr.readyState ||
                                (200 != r.xhr.status && 0 != r.xhr.status)
                              )
                                r.xhr.status >= 400 &&
                                  ((r.currentUrl = r.xhr.responseURL),
                                  r.ShowDebug("! OnSubmitError(" + e + ")"),
                                  "function" == typeof r.OnSubmitError &&
                                    r.OnSubmitError(e),
                                  r.ShowDebug("! OnSubmitEnd(" + e + ")"),
                                  "function" == typeof r.OnSubmitEnd &&
                                    r.OnSubmitEnd(e),
                                  (r.asyncInProgress = !1));
                              else {
                                r.currentUrl = r.xhr.responseURL;
                                var t = r.xhr.responseText,
                                  n = t.match(
                                    /(<script>)?window\.location\.href='(.*?)';(<\/script>)?/i
                                  ),
                                  i = !1,
                                  s = "";
                                null != n && n.length > 0
                                  ? ((i = !0),
                                    (s = n[0]
                                      .replace(
                                        "<script>window.location.href='",
                                        ""
                                      )
                                      .replace("';</script>", "")
                                      .replace("window.location.href='", "")
                                      .replace("';", "")))
                                  : (r.container.innerHTML = t),
                                  r.ShowDebug("! OnSubmitSuccess(" + e + ")"),
                                  "function" == typeof r.OnSubmitSuccess &&
                                    r.OnSubmitSuccess(e),
                                  (r.container.getElementsByClassName(
                                    "formCompleted"
                                  ).length > 0 ||
                                    1 == i) &&
                                    (r.ShowDebug(
                                      "! OnSubmitDataSuccess(" + e + ")"
                                    ),
                                    "function" ==
                                      typeof r.OnSubmitDataSuccess &&
                                      r.OnSubmitDataSuccess(e)),
                                  r.container.getElementsByClassName(
                                    "formErrorMessage"
                                  ).length > 0 &&
                                    (r.ShowDebug(
                                      "! OnSubmitDataError(" + e + ")"
                                    ),
                                    "function" == typeof r.OnSubmitDataError &&
                                      r.OnSubmitDataError(e)),
                                  r.ShowDebug("! OnSubmitEnd(" + e + ")"),
                                  "function" == typeof r.OnSubmitEnd &&
                                    r.OnSubmitEnd(e),
                                  (r.asyncInProgress = !1),
                                  0 == i
                                    ? (r.InitSubmitButton(), r.ShowError())
                                    : (r.ShowDebug(
                                        "! OnSubmitRedirection(" +
                                          e +
                                          "," +
                                          s +
                                          ")"
                                      ),
                                      "function" ==
                                        typeof r.OnSubmitRedirection &&
                                        r.OnSubmitRedirection(e, s),
                                      (window.location.href = s));
                              }
                            }),
                            "survey" == this.OperationType &&
                            void 0 !== this.currentUrl &&
                            null != this.currentUrl &&
                            "" != this.currentUrl
                              ? this.xhr.open("POST", this.currentUrl, !0)
                              : this.xhr.open("POST", this.url, !0),
                            this.xhr.send(s);
                        } else
                          r.ShowDebug("! OnSubmitStartError(" + e + ")"),
                            "function" == typeof r.OnSubmitStartError &&
                              r.OnSubmitStartError(e),
                            (r.asyncInProgress = !1);
                    },
                  },
                  {
                    key: "InitSubmitButton",
                    value: function InitSubmitButton() {
                      this.ShowDebug("InitSubmitButton");
                      var t = this;
                      try {
                        var e = this.container.getElementsByClassName(
                          "formSubmit"
                        );
                        e.length > 0 &&
                          ((e = e[0]),
                          e.getElementsByTagName("input").length > 0
                            ? (this.submitButton = e.getElementsByTagName(
                                "input"
                              )[0])
                            : (this.submitButton = e.getElementsByTagName(
                                "a"
                              )[0]),
                          this.submitButton.removeAttribute("onclick"),
                          this.submitButton.addEventListener(
                            "click",
                            function (e) {
                              ("40003" !== t.AccountId &&
                                40003 !== t.AccountId) ||
                                (t.submitButton.innerHTML =
                                  '<span class="mb-form-loader"></span>'),
                                t.Submit(e);
                            }.bind(t),
                            !1
                          ));
                      } catch (t) {}
                      try {
                        var r = this.container.getElementsByClassName(
                          "formPagerNext"
                        );
                        if (r.length > 0) {
                          r = r[0];
                          var n = void 0;
                          (n =
                            r.getElementsByTagName("input").length > 0
                              ? r.getElementsByTagName("input")[0]
                              : r.getElementsByTagName("a")[0]),
                            n.removeAttribute("onclick"),
                            n.addEventListener(
                              "click",
                              function (e) {
                                (document.getElementById("status").value =
                                  "next"),
                                  t.Submit(e, "next");
                              }.bind(t),
                              !1
                            );
                        }
                      } catch (t) {}
                      try {
                        var i = this.container.getElementsByClassName(
                          "formPagerPrevious"
                        );
                        if (i.length > 0) {
                          i = i[0];
                          var s = void 0;
                          (s =
                            i.getElementsByTagName("input").length > 0
                              ? i.getElementsByTagName("input")[0]
                              : i.getElementsByTagName("a")[0]),
                            s.removeAttribute("onclick"),
                            s.addEventListener(
                              "click",
                              function (e) {
                                (document.getElementById("status").value =
                                  "previous"),
                                  t.Submit(e, "previous");
                              }.bind(t),
                              !1
                            );
                        }
                      } catch (t) {}
                    },
                  },
                  {
                    key: "GetXMLHttpRequest",
                    value: function GetXMLHttpRequest() {
                      var t = null;
                      if (!window.XMLHttpRequest && !window.ActiveXObject)
                        return (
                          alert(
                            "Your browser does not support the XMLHTTPRequest object..."
                          ),
                          null
                        );
                      if (window.ActiveXObject)
                        try {
                          t = new ActiveXObject("Msxml2.XMLHTTP");
                        } catch (e) {
                          t = new ActiveXObject("Microsoft.XMLHTTP");
                        }
                      else t = new XMLHttpRequest();
                      return t;
                    },
                  },
                  {
                    key: "GetParameterByName",
                    value: function GetParameterByName(t) {
                      var e = this.GetParameters(),
                        r = null;
                      return (
                        void 0 !== e &&
                          Array.isArray(e) &&
                          e.forEach(function (e) {
                            e.name == t && (r = e.value);
                          }),
                        r
                      );
                    },
                  },
                  {
                    key: "GetParameters",
                    value: function GetParameters() {
                      var t = [],
                        e = window.location.href.split("#"),
                        r = e[0].replace(/[?&]+([^=&]+)=([^&]*)/gi, function (
                          e,
                          r,
                          n
                        ) {
                          t.push({ name: r, value: n });
                        });
                      return t;
                    },
                  },
                  {
                    key: "ShowDebug",
                    value: function ShowDebug(t) {
                      if (
                        1 == this.Debug &&
                        "undefined" != typeof console &&
                        void 0 !== console.debug
                      ) {
                        var e = new Date(),
                          r =
                            e.getHours() +
                            "h " +
                            e.getMinutes() +
                            "m " +
                            e.getSeconds() +
                            "s " +
                            e.getMilliseconds() +
                            "ms";
                        console.debug(r + " | " + this.ContainerId + " | " + t);
                      }
                    },
                  },
                ]),
                MB_Form_JsApp
              );
            })();
          e.exports = i;
        },
        {},
      ],
    },
    {},
    [1]
  )(1);
});
