// expect: * accept
// source: issue #40/#41 shape B (invented), 8 blocks, names declared
codeunit 50000 "Shape B"
{
    procedure P(var G: Boolean; M0: Boolean; M1: Boolean; M2: Boolean; M3: Boolean; M4: Boolean; M5: Boolean; M6: Boolean)
    begin
if M0 then begin
  begin
#if not X
        if G then S2() else begin
            T();
        end;
#endif
  end
end else if M1 then begin
  begin
#if not X
        if G then S2() else begin
            T();
        end;
#endif
  end
end else if M2 then begin
  begin
#if not X
        if G then S2() else begin
            T();
        end;
#endif
  end
end else if M3 then begin
  begin
#if not X
        if G then S2() else begin
            T();
        end;
#endif
  end
end else if M4 then begin
  begin
#if not X
        if G then S2() else begin
            T();
        end;
#endif
  end
end else if M5 then begin
  begin
#if not X
        if G then S2() else begin
            T();
        end;
#endif
  end
end else if M6 then begin
  begin
#if not X
        if G then S2() else begin
            T();
        end;
#endif
  end
end else begin
  begin
#if not X
        if G then S2() else begin
            T();
        end;
#endif
  end
end
    end;

    local procedure S2()
    begin
    end;

    local procedure T()
    begin
    end;
}
